/**
 * Daily Amazon Product Opportunities Analysis
 * Free data sources: Google Trends (no API needed)
 * 
 * Strategy:
 * 1. Fetch ALL Google Trends (no filtering)
 * 2. For EVERY trend, try to map relevant Amazon products
 * 3. Score and rank by opportunity potential
 */

import { writeFileSync, mkdirSync, appendFileSync } from 'fs';

const WORKDIR = '/root/.openclaw/workspace';
const LOG_FILE = `${WORKDIR}/logs/amazon-opportunities.log`;

function log(msg) {
    const timestamp = new Date().toISOString();
    const line = `[${timestamp}] ${msg}\n`;
    try { appendFileSync(LOG_FILE, line); } catch (e) {}
    console.log(msg);
}

function decodeHtmlEntities(text) {
    return text
        .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ');
}

// Fetch Google Trends RSS - THIS WORKS (free)
async function fetchTrends() {
    try {
        const response = await fetch('https://trends.google.com/trending/rss?geo=US', {
            headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' }
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const xml = await response.text();
        const items = [];
        
        const itemRegex = /<item>([\s\S]*?)<\/item>/gi;
        let itemMatch;
        while ((itemMatch = itemRegex.exec(xml)) !== null) {
            const itemXml = itemMatch[1];
            
            const titleMatch = /<title>(.*?)<\/title>/i.exec(itemXml);
            const trafficMatch = /<ht:approx_traffic>(.*?)<\/ht:approx_traffic>/i.exec(itemXml);
            
            const title = titleMatch ? decodeHtmlEntities(titleMatch[1]) : '';
            const traffic = trafficMatch ? decodeHtmlEntities(trafficMatch[1]) : '';
            
            const newsItems = [];
            const newsItemRegex = /<ht:news_item>([\s\S]*?)<\/ht:news_item>/gi;
            let newsMatch;
            while ((newsMatch = newsItemRegex.exec(itemXml)) !== null) {
                const newsXml = newsMatch[1];
                const newsTitle = /<ht:news_item_title>(.*?)<\/ht:news_item_title>/i.exec(newsXml);
                const newsSnippet = /<ht:news_item_snippet>(.*?)<\/ht:news_item_snippet>/i.exec(newsXml);
                const newsSource = /<ht:news_item_source>(.*?)<\/ht:news_item_source>/i.exec(newsXml);
                
                newsItems.push({
                    title: newsTitle ? decodeHtmlEntities(newsTitle[1]) : '',
                    snippet: newsSnippet ? decodeHtmlEntities(newsSnippet[1]) : '',
                    source: newsSource ? decodeHtmlEntities(newsSource[1]) : ''
                });
            }
            
            if (title) items.push({ title, traffic, newsItems });
        }
        
        log(`Fetched ${items.length} trends`);
        return items;
        
    } catch (error) {
        log(`Error fetching trends: ${error.message}`);
        return [];
    }
}

// 中英对照词典 - 趋势词中文解释
const trendTranslations = {
    // ========== AI/科技 ==========
    'ai': '人工智能/AI',
    'chatgpt': 'ChatGPT - OpenAI开发的AI聊天机器人',
    'gpt': 'GPT - OpenAI的AI语言模型',
    'llm': '大型语言模型 (Large Language Model)',
    'artificial intelligence': '人工智能 (AI)',
    'copilot': 'GitHub Copilot - AI编程助手',
    'gemini': 'Google Gemini - AI大模型',
    'claude': 'Claude - Anthropic开发的AI助手',
    'openai': 'OpenAI - AI研究公司',
    'anthropic': 'Anthropic - AI安全研究公司',
    'midjourney': 'Midjourney - AI图像生成工具',
    'stable diffusion': 'Stable Diffusion - AI图像生成模型',
    'perplexity': 'Perplexity - AI搜索/问答引擎',
    'cursor': 'Cursor - AI代码编辑器',
    'windsurf': 'Windsurf - AI代码编辑器',
    'notion': 'Notion - 笔记/知识管理工具',
    // ========== 股票/财经 ==========
    'stock market': '股票市场 - 股市行情',
    'stock price': '股票价格',
    'stock': '股票 - stock',
    'dow jones': '道琼斯指数 - 美国股市基准',
    'nasdaq': '纳斯达克指数 - 科技股集中交易所',
    's&p 500': '标普500指数 - 美国500强股票指数',
    'nvidia': '英伟达 - AI芯片巨头 (NVDA)',
    'nvidia stock': '英伟达股票 (NVDA) - AI芯片龙头',
    'apple stock': '苹果股票 (AAPL)',
    'amazon stock': '亚马逊股票 (AMZN)',
    'tesla stock': '特斯拉股票 (TSLA)',
    'google stock': '谷歌股票 (GOOGL)',
    'microsoft stock': '微软股票 (MSFT)',
    'meta stock': 'Meta/Facebook股票 (META)',
    'netflix stock': 'Netflix股票 (NFLX)',
    'amd stock': 'AMD股票 (AMD)',
    'intel stock': '英特尔股票 (INTC)',
    ' recession': '经济衰退',
    'inflation': '通货膨胀',
    'interest rate': '利率',
    'federal reserve': '美联储',
    'dollar': '美元',
    'gold price': '黄金价格',
    'oil price': '油价',
    'gas price': '汽油价格',
    'cryptocurrency': '加密货币',
    'bitcoin': '比特币 (BTC)',
    'ethereum': '以太坊 (ETH)',
    // ========== 名人/明星 ==========
    'kylie jenner': '凯莉·詹娜 - 卡戴珊家族成员/美妆大亨',
    'taylor swift': '泰勒·斯威夫特 - 歌手/霉霉',
    'kim kardashian': '金·卡戴珊 - 真人秀明星/商业巨头',
    'elon musk': '埃隆·马斯克 - 特斯拉/SpaceX CEO',
    'beyonce': '碧昂斯 - 歌手',
    'rihanna': '蕾哈娜 - 歌手/美妆品牌',
    'oprah': '奥普拉 - 脱口秀主持人',
    'dwayne johnson': '道恩·强森/巨石强森 - WWE明星转行演员',
    'john cena': '约翰·塞纳 - WWE摔角明星',
    'dave grohl': 'Dave Grohl - Foo Fighters主唱',
    'kurt cobain': '柯特·柯本 - Nirvana乐队主唱',
    'beyonce tour': '碧昂斯巡回演唱会',
    'taylor swift eras tour': '泰勒·斯威夫特时代巡回演唱会',
    // ========== 电影/电视 ==========
    'movie': '电影',
    'netflix': 'Netflix流媒体平台',
    'prime video': 'Amazon Prime Video',
    'disney plus': 'Disney+流媒体',
    'hulu': 'Hulu流媒体',
    'box office': '票房',
    '(movie) release': '电影上映',
    '(tv) series': '电视剧',
    'season finale': '季终集',
    'streaming': '流媒体/直播',
    // ========== 游戏 ==========
    'video game': '电子游戏',
    'gaming': '游戏/游戏相关',
    'xbox': 'Xbox微软游戏机',
    'playstation': 'PlayStation索尼游戏机',
    'nintendo': 'Nintendo任天堂',
    'ps5': 'PS5游戏机',
    'xbox series': 'Xbox Series X游戏机',
    'switch': 'Nintendo Switch游戏机',
    'minecraft': 'Minecraft我的世界',
    'fortnite': 'Fortnite堡垒之夜',
    'call of duty': '使命召唤游戏',
    'gta': '侠盗猎车手游戏',
    'zelda': '塞尔达传说游戏',
    'mario': '马里奥游戏',
    'pokemon': '宝可梦/精灵宝可梦',
    // ========== 音乐 ==========
    'concert': '音乐会/演唱会',
    'album': '专辑',
    'song': '歌曲',
    'music': '音乐',
    'tour': '巡回演唱会',
    'billboard': 'Billboard音乐排行榜',
    'spotify': 'Spotify音乐流媒体',
    'apple music': 'Apple Music音乐服务',
    // ========== 体育 ==========
    'nba': 'NBA美国职业篮球',
    'nfl': 'NFL美国职业橄榄球',
    'mlb': 'MLB美国职业棒球',
    'nhl': 'NHL国家冰球联盟',
    'super bowl': '超级碗 - NFL总决赛',
    'world series': '世界大赛 - MLB总决赛',
    'nba finals': 'NBA总决赛',
    'nfl playoffs': 'NFL季后赛',
    'march madness': 'NCAA疯狂三月篮球赛',
    'olympics': '奥运会',
    'world cup': '世界杯',
    'us open': '美国网球公开赛',
    'wimbledon': '温布尔登网球锦标赛',
    'masters': '大师赛/高尔夫美国大师赛',
    'lakers': '湖人队 - NBA',
    'warriors': '勇士队 - NBA',
    'celtics': '凯尔特人队 - NBA',
    'yankees': '洋基队 - MLB',
    'dodgers': '道奇队 - MLB',
    'cowboys': '牛仔队 - NFL',
    'chiefs': '酋长队 - NFL',
    'lebron': '勒布朗·詹姆斯 - NBA球星',
    'stephen curry': '斯蒂芬·库里 - NBA球星',
    'messi': '梅西 - 足球巨星',
    'ronaldo': 'C罗 - 足球巨星',
    'mahomes': '帕特里克·马霍姆斯 - NFL球星',
    // ========== 天气/自然灾害 ==========
    'weather': '天气',
    'hurricane': '飓风',
    'tornado': '龙卷风',
    'earthquake': '地震',
    'flood': '洪水',
    'storm': '暴风雨',
    'snow': '降雪',
    'blizzard': '暴风雪',
    'heat wave': '热浪',
    'california wildfire': '加州山火',
    // ========== 新闻/事件 ==========
    'trump': '特朗普 - 美国前总统',
    'biden': '拜登 - 美国总统',
    'election': '美国大选',
    'congress': '美国国会',
    'supreme court': '最高法院',
    'ukraine': '乌克兰/俄乌战争',
    'israel': '以色列/中东局势',
    'iran': '伊朗/核问题',
    'china': '中国/美中关系',
    'north korea': '朝鲜/金正恩',
    'russia': '俄罗斯/普京',
    'breaking news': '突发新闻',
    'shooting': '枪击事件',
    'protest': '抗议活动',
    // ========== 品牌/产品 ==========
    'apple': '苹果公司 (AAPL)',
    'samsung': '三星电子',
    'google': '谷歌 (GOOGL)',
    'amazon': '亚马逊 (AMZN)',
    'microsoft': '微软 (MSFT)',
    'dyson': '戴森 - 高端家电品牌',
    'nike': '耐克 - 运动品牌',
    'adidas': '阿迪达斯 - 运动品牌',
    'lululemon': 'Lululemon - 瑜伽运动服',
    'starbucks': '星巴克咖啡',
    'mcdonald': '麦当劳',
    // ========== 通用 ==========
    'deals': '优惠/折扣',
    'sale': '促销/打折',
    'clearance': '清仓特卖',
    'black friday': '黑色星期五购物节',
    'cyber monday': '网络星期一',
    'prime day': '亚马逊会员日',
    'gift': '礼物',
    'gift guide': '礼品指南',
    'review': '评测/评论',
    'best': '最佳/最好',
    'top': '顶级/排行榜',
    'cheap': '便宜/低价',
    'free': '免费',
    'how to': '如何做/教程',
    'what is': '什么是',
    'why': '为什么',
    'recipe': '食谱/菜谱',
    'diy': '自己动手/DIY',
    'tutorial': '教程',
    'tips': '技巧/小贴士',
    'amazon': '亚马逊购物',
    'best seller': '畅销产品',
    'viral': '爆红/病毒式传播',
    'trending': '热门/趋势',
    // 音频设备
    'headphone': '耳机',
    'earbud': '无线耳塞/耳麦',
    'speaker': '音箱/扬声器',
    'audio': '音频设备',
    'sound': '音频/声音',
    'music': '音乐',
    'podcast': '播客/音频节目',
    'airpod': 'AirPods - 苹果无线耳机',
    'beats': 'Beats -  Beats耳机品牌',
    'bose': 'Bose - 高端音响品牌',
    'sony headphones': '索尼耳机',
    'noise cancelling': '降噪功能',
    'alexa': 'Alexa - 亚马逊语音助手',
    'echo': 'Amazon Echo - 智能音箱',
    'siri': 'Siri - 苹果语音助手',
    'jbl': 'JBL - 音响品牌',
    'sonos': 'Sonos - 智能音响系统',
    'soundbar': '条形音箱/声吧',
    // 手机/平板
    'iphone': 'iPhone - 苹果手机',
    'samsung': '三星',
    'galaxy': 'Galaxy - 三星手机系列',
    'pixel': 'Google Pixel - 安卓手机',
    'android': '安卓系统',
    'apple': '苹果公司',
    'smartphone': '智能手机',
    'tablet': '平板电脑',
    'ipad': 'iPad - 苹果平板电脑',
    'oneplus': '一加手机',
    'magsafe': 'MagSafe - 苹果磁吸充电',
    'spigen': 'Spigen - 手机配件品牌',
    'anker': 'Anker - 充电器/配件品牌',
    // 电脑/配件
    'laptop': '笔记本电脑',
    'macbook': 'MacBook - 苹果笔记本',
    'thinkpad': 'ThinkPad - 联想商务笔记本',
    'dell': '戴尔电脑',
    'hp': '惠普电脑',
    'chromebook': 'Chromebook - 谷歌笔记本',
    'surface': 'Surface - 微软平板/笔记本',
    'asus': '华硕',
    'razer': 'Razer - 游戏设备品牌',
    'alienware': 'Alienware - 戴尔游戏电脑',
    'laptop stand': '笔记本支架',
    'usb-c hub': 'USB-C扩展坞',
    'mechanical keyboard': '机械键盘',
    'gaming mouse': '游戏鼠标',
    'ssd': '固态硬盘',
    'monitor': '显示器',
    // 智能家居
    'smart home': '智能家居',
    'google home': 'Google Home - 谷歌智能音箱',
    'nest': 'Nest - 谷歌智能家居品牌',
    'ring': 'Ring - 智能门铃品牌',
    'smart plug': '智能插座',
    'smart light': '智能灯具',
    'homepod': 'HomePod - 苹果智能音箱',
    'smart lock': '智能门锁',
    'camera': '摄像头/相机',
    'thermostat': '智能恒温器',
    'philips hue': '飞利浦Hue智能灯具',
    'tp-link': 'TP-Link - 网络设备品牌',
    // 游戏
    'playstation': 'PlayStation - 索尼游戏机',
    'xbox': 'Xbox - 微软游戏机',
    'nintendo': 'Nintendo - 任天堂游戏机',
    'gaming': '游戏/游戏相关',
    'gamer': '游戏玩家',
    'ps5': 'PS5 - PlayStation 5',
    'steam deck': 'Steam Deck - 蒸汽掌机',
    'gaming chair': '电竞椅',
    'controller': '游戏手柄',
    'switch': 'Switch - 任天堂游戏机',
    'fortnite': 'Fortnite - 热门游戏',
    'minecraft': 'Minecraft - 我的世界游戏',
    'gaming headset': '游戏耳机',
    // 健身/健康
    'fitness': '健身/健康',
    'workout': '锻炼/健身',
    'exercise': '运动/锻炼',
    'gym': '健身房',
    'running': '跑步/跑步运动',
    'yoga': '瑜伽',
    'health': '健康',
    'fitbit': 'Fitbit - 健身追踪器',
    'garmin': 'Garmin - 运动手表品牌',
    'smartwatch': '智能手表',
    'apple watch': 'Apple Watch - 苹果智能手表',
    'weight loss': '减肥/减重',
    'training': '训练/培训',
    'sports': '体育/运动',
    'resistance band': '阻力带/弹力带',
    'foam roller': '泡沫轴/瑜伽柱',
    'yoga mat': '瑜伽垫',
    'kettlebell': '壶铃',
    'dumbbell': '哑铃',
    // 摄影/摄像
    'camera': '相机/摄影',
    'canon': '佳能相机',
    'nikon': '尼康相机',
    'sony camera': '索尼相机',
    'gimbal': '手持云台/稳定器',
    'drone': '无人机',
    'youtube': 'YouTube - 视频平台',
    'content creator': '内容创作者',
    'streaming': '直播/流媒体',
    'video': '视频',
    'photo': '照片/摄影',
    'gopro': 'GoPro - 运动相机',
    'insta360': 'Insta360 - 全景相机',
    'ring light': '补光灯/环形灯',
    'microphone': '麦克风',
    'elgato': 'Elgato - 直播设备品牌',
    // 生活/家电
    'coffee': '咖啡',
    'espresso': '意式浓缩咖啡',
    'air fryer': '空气炸锅',
    'instant pot': '多功能压力锅',
    'robot vacuum': '扫地机器人',
    'dyson': 'Dyson - 戴森家电品牌',
    'kitchen': '厨房/厨具',
    'cooking': '烹饪/做饭',
    'cleaning': '清洁/打扫',
    'vacuum': '吸尘器',
    'tea': '茶',
    'blender': '搅拌机/破壁机',
    'juice': '果汁',
    'nespresso': 'Nespresso - 胶囊咖啡机',
    'vitamix': 'Vitamix - 高端搅拌机',
    'roomba': 'Roomba - iRobot扫地机器人',
    'instant pot': 'Instant Pot - 多功能锅',
    // 网络安全
    'vpn': 'VPN - 虚拟专用网络',
    'password': '密码',
    'security': '安全/安防',
    'privacy': '隐私',
    'hack': '黑客/入侵',
    'breach': '数据泄露',
    'malware': '恶意软件',
    'encryption': '加密',
    'cyber': '网络/网络安全',
    'antivirus': '杀毒软件',
    'firewall': '防火墙',
    'nordvpn': 'NordVPN - VPN服务',
    '1password': '1Password - 密码管理器',
    'yubikey': 'YubiKey - 硬件安全密钥',
    'lastpass': 'LastPass - 密码管理器',
    'bitwarden': 'Bitwarden - 开源密码管理器',
    'norton': 'Norton - 诺顿杀毒软件',
    // 教育
    'course': '课程',
    'udemy': 'Udemy - 在线课程平台',
    'coursera': 'Coursera - 在线教育平台',
    'skill': '技能',
    'learning': '学习',
    'certificate': '证书',
    'degree': '学位',
    'education': '教育',
    'training': '培训',
    'book': '书籍',
    'kindle': 'Kindle - 亚马逊电子书阅读器',
    'reading': '阅读',
    'study': '学习',
    'skillshare': 'Skillshare - 技能分享平台',
    'masterclass': 'MasterClass - 大师课程',
    'linkedin learning': 'LinkedIn Learning - 在线学习',
    // 玩具/游戏
    'toy': '玩具',
    'game': '游戏',
    'lego': '乐高',
    'kids': '儿童/孩子',
    'children': '儿童/孩子',
    'board game': '桌游/棋盘游戏',
    'puzzle': '拼图/谜题',
    'play': '玩耍',
    'baby': '婴儿/宝宝',
    'gift': '礼物',
    'present': '礼物',
    'birthday': '生日',
    'nerf': 'NERF - 玩具枪品牌',
    'melissa doug': 'Melissa & Doug - 儿童玩具品牌',
    'play-doh': '培乐多 - 橡皮泥玩具',
    // 美妆
    'beauty': '美妆/美容',
    'skincare': '护肤',
    'makeup': '化妆品/彩妆',
    'cosmetic': '化妆品',
    'skin': '皮肤',
    'hair': '头发/美发',
    'nail': '美甲',
    'perfume': '香水',
    'fragrance': '香水/香氛',
    'wellness': '健康养生',
    'serum': '精华液',
    'moisturizer': '保湿霜/润肤霜',
    'vitamin c': '维生素C',
    // 时尚
    'fashion': '时尚',
    'clothing': '服装',
    'shoes': '鞋子',
    'sneakers': '运动鞋/休闲鞋',
    'jordan': 'Jordan - 乔丹球鞋',
    'nike': 'Nike - 耐克',
    'adidas': 'Adidas - 阿迪达斯',
    'hoodie': '卫衣/帽衫',
    'jacket': '外套/夹克',
    'watch': '手表',
    'sunglasses': '太阳镜/墨镜',
    'bag': '包/背包',
    'levi': "Levi's - 李维斯牛仔裤",
    'ray-ban': 'Ray-Ban - 雷朋眼镜',
    'casio': 'Casio - 卡西欧手表',
    'north face': 'The North Face - 户外服装品牌',
    // 户外
    'camping': '露营',
    'hiking': '徒步/远足',
    'outdoor': '户外/野外',
    'fishing': '钓鱼',
    'biking': '骑行/自行车',
    'cycling': '自行车/骑行',
    'climbing': '攀岩',
    'tent': '帐篷',
    'backpack': '背包',
    'portable power': '便携电源/移动电源',
    'solar charger': '太阳能充电器',
    'bike helmet': '自行车头盔',
    // 体育
    'sports': '体育运动',
    'nba': 'NBA - 美国职业篮球联赛',
    'nfl': 'NFL - 美国职业橄榄球联盟',
    'mlb': 'MLB - 美国职业棒球大联盟',
    'nhl': 'NHL - 国家冰球联盟',
    'super bowl': '超级碗 - NFL总决赛',
    'world series': '世界大赛 - MLB总决赛',
    'basketball': '篮球',
    'football': '橄榄球/足球',
    'baseball': '棒球',
    'soccer': '足球',
    'tennis': '网球',
    'golf': '高尔夫',
    'boxing': '拳击',
    'ufc': 'UFC - 终极格斗冠军赛',
    'mma': 'MMA - 混合武术',
    'wwe': 'WWE - 世界摔角娱乐',
    'wrestling': '摔跤',
    'volleyball': '排球',
    'swimming': '游泳',
    'marathon': '马拉松',
    'skiing': '滑雪',
    'snowboarding': '单板滑雪',
    'surfing': '冲浪',
    'lakers': '湖人队',
    'warriors': '勇士队',
    'celtics': '凯尔特人队',
    'yankees': '洋基队',
    'dodgers': '道奇队',
    'cowboys': '牛仔队',
    'eagles': '老鹰队',
    'chiefs': '酋长队',
    'packers': '包装工队',
    'march madness': 'NCAA疯狂三月',
    'olympics': '奥运会',
    'world cup': '世界杯',
    'stanley cup': '斯坦利杯',
    'lebron': '勒布朗詹姆斯',
    'messi': '梅西',
    'ronaldo': 'C罗',
    'mahomes': '帕特里克马霍姆斯',
    'jersey': '球衣',
    'sports gear': '运动装备',
    'sports equipment': '运动设备',
    'sports memorabilia': '体育纪念品',
    'trading cards': '球星卡',
    // 汽车
    'car': '汽车',
    'auto': '汽车/自动',
    'vehicle': '车辆',
    'driving': '驾驶',
    'dash cam': '行车记录仪',
    'tire': '轮胎',
    'oil': '机油',
    'tesla': '特斯拉',
    'electric vehicle': '电动汽车',
    'ev': '电动汽车',
    'charger': '充电器',
    'jump starter': '汽车应急启动电源',
    'car vacuum': '车载吸尘器',
    // 通用
    'trending': '热门/趋势',
    'viral': '病毒式传播/爆红',
    'popular': '流行/受欢迎',
    'best seller': '畅销产品',
    'top rated': '高评分产品',
    'prime day': '亚马逊会员日',
    'black friday': '黑色星期五',
    'cyber monday': '网络星期一',
    'holiday gift': '节日礼物',
    'gift guide': '礼品指南',
    'eco friendly': '环保产品',
    'sustainable': '可持续产品',
    'portable': '便携式',
    'wireless': '无线',
    'bluetooth': '蓝牙',
    'smart': '智能',
    'mini': '迷你/小型',
    'pro': '专业版/Pro版',
    'max': '最大/顶配版',
    'ultra': 'Ultra - 超高端版本',
    'plus': 'Plus - 增强版',
    'lite': 'Lite - 轻量版',
    'max': 'Max - 最大版'
};

// ========== 用户偏好过滤 (2026-03-17) ==========
// David 不感兴趣的领域
const excludeCategories = [
    // 体育 - David明确不感兴趣
    'sports', 'nba', 'nfl', 'mlb', 'nhl', 'basketball', 'football', 'baseball', 'soccer', 'tennis', 'golf', 'boxing', 'ufc', 'mma', 'wwe', 'wrestling', 'volleyball', 'swimming',
    'lakers', 'warriors', 'celtics', 'yankees', 'dodgers', 'cowboys', 'eagles', 'chiefs', 'packers', '49ers', 'raiders', 'bears', 'patriots', 'buccaneers', 'ravens', 'bengals',
    'lebron', 'jordan', 'curry', 'messi', 'ronaldo', 'mahomes', 'ohtani', 'trede', 'wembanyama',
    'march madness', 'super bowl', 'world series', 'nba finals', 'nfl playoffs', 'world cup', 'olympics', 'us open', 'wimbledon', 'masters', 'stanley cup',
    // 娱乐/名人/综艺 - 扩展名单
    'celebrity', 'famous', 'star', 'actor', 'actress', 'singer', 'rapper', 'musician', 'dancer', 'influencer',
    'reality tv', '真人秀', '综艺', 'kardashian', 'jenner', 'j Bieber', 'swift', 'beyonce', 'rihanna', 'drake', 'kanye', 'taylor',
    'movie star', 'hollywood', 'netflix show', 'tv series finale', 'season finale', 'breaking bad', 'stranger things',
    // WWE/摔角 - David明确不感兴趣
    'wwe', 'wrestling', 'roman reigns', 'randy orton', 'aj styles', 'seth rollins', 'brock lesnar', 'john cena', 'the rock', 'aew',
    // 政治新闻 - David可能不感兴趣
    'trump', 'biden', 'election', 'congress', 'supreme court', 'senate', 'democrat', 'republican', 'polling',
    // 负面新闻/灾难
    'shooting', 'murder', 'death', 'crash', 'accident', 'disaster', 'tragedy', 'terror', 'attack',
    // 游戏相关
    'esports', 'gaming tournament', 'twitch', 'streamer',
    // 名人名字 - 扩展检测
    'lauren conrad', 'dakota fanning', 'jennie garth', 'whitney leavitt', 'rob wright', 'konnor griffin', 'beirut',
    'kim kardashian', 'kylie jenner', 'khloe kardashian', 'kourtney kardashian', 'kendall jenner',
    'tom brady', 'selena gomez', 'ariana grande', 'justin bieber', 'lady gaga', 'brad pitt', 'angelina jo',
    'jennifer lopez', 'beyonce', 'rihanna', 'kanye west', 'drake', 'eminem', 'taylor swift',
    'dulux', 'nadine', 'bobby', 'emma stone', 'ryan reynolds', 'margot robbie',
];

// 额外的名人检测 - 常见名人名字模式
const celebrityPatterns = [
    /^lauren conrad$/i,
    /^dakota fanning$/i,
    /^jennie garth$/i,
    /^whitney leavitt$/i,
    /^rob wright$/i,
    /^konnor griffin$/i,
    /^beirut$/i,
];

// 检查趋势是否应该被过滤
function shouldExclude(trendText) {
    const lower = trendText.toLowerCase();
    
    // Check against exclude list
    for (const keyword of excludeCategories) {
        if (lower.includes(keyword.toLowerCase())) {
            return true;
        }
    }
    
    // Check celebrity name patterns (two-word proper names that are likely celebrities)
    for (const pattern of celebrityPatterns) {
        if (pattern.test(trendText)) {
            return true;
        }
    }
    
    // Additional heuristic: if it's a single name with spaces (Firstname Lastname format)
    // and it's short, it might be a celebrity
    const words = trendText.trim().split(/\s+/);
    if (words.length === 2) {
        // Two-word name that's not obviously a product/trend
        // Common product patterns would have numbers, 'vs', 'review' etc
        const hasProductSignal = lower.includes('review') || lower.includes('vs') || 
                                 lower.includes('best') || lower.includes('top') ||
                                 lower.includes('stock') || lower.includes('price') ||
                                 lower.includes('deal') || lower.includes('sale');
        if (!hasProductSignal && words[0].length > 2 && words[1].length > 2) {
            // Likely a person's name - exclude
            return true;
        }
    }
    
    return false;
}

// 获取趋势的背景解释
function getTrendBackground(trendText) {
    const lower = trendText.toLowerCase();
    
    // 股票财经 - 使用单词边界匹配
    if (lower.includes('stock')) {
        const stockMatch = lower.match(/\b(nvidia|apple|amazon|tesla|google|microsoft|meta|netflix|amd|intel)\b/);
        if (stockMatch) {
            const stockMap = {
                'nvidia': '英伟达 (NVDA) - AI芯片龙头',
                'apple': '苹果 (AAPL)',
                'amazon': '亚马逊 (AMZN)',
                'tesla': '特斯拉 (TSLA)',
                'google': '谷歌 (GOOGL)',
                'microsoft': '微软 (MSFT)',
                'meta': 'Meta (META)',
                'netflix': 'Netflix (NFLX)',
                'amd': 'AMD',
                'intel': '英特尔 (INTC)',
            };
            return stockMap[stockMatch[1].toLowerCase()];
        }
    }
    
    // AI科技 - 使用单词边界匹配
    const aiMatch = lower.match(/\b(ai|chatgpt|gpt-|gemini|claude|openai|anthropic|midjourney|copilot)\b/);
    if (aiMatch) {
        const aiMap = {
            'ai': 'AI人工智能',
            'chatgpt': 'ChatGPT - OpenAI AI聊天',
            'gpt-': 'GPT - OpenAI语言模型',
            'gemini': 'Google Gemini - AI大模型',
            'claude': 'Claude - Anthropic AI',
            'openai': 'OpenAI - AI研究公司',
            'anthropic': 'Anthropic - AI安全公司',
            'midjourney': 'Midjourney - AI绘图',
            'copilot': 'GitHub Copilot - AI编程',
        };
        return aiMap[aiMatch[1].toLowerCase()];
    }
    
    // 天气相关
    if (lower.includes('weather') || lower.includes('temperature') || lower.includes('forecast')) {
        return '天气查询 - 季节性需求，可能带动相关产品'
    }
    
    // 折扣优惠
    if (lower.includes('deal') || lower.includes('steal') || lower.includes('sale') || lower.includes('coupon') || lower.includes('discount')) {
        return '折扣优惠 - 消费者比价购物高峰'
    }
    
    // 产品评测
    if (lower.includes('review') || lower.includes('unboxing') || lower.includes('vs') || lower.includes('versus')) {
        return '产品对比评测 - 用户研究购买决策'
    }
    
    // 智能家居
    if (lower.includes('smart home') || lower.includes('alexa') || lower.includes('echo') || lower.includes('google home') || lower.includes('nest')) {
        return '智能家居 - Amazon Echo/Google Home类设备'
    }
    
    // 消费电子
    if (lower.includes('iphone') || lower.includes('ipad') || lower.includes('macbook') || lower.includes('samsung') || lower.includes('pixel')) {
        return '消费电子 - 手机/平板/电脑配件'
    }
    
    // 游戏设备
    if (lower.includes('ps5') || lower.includes('xbox') || lower.includes('switch') || lower.includes('steam deck')) {
        return '游戏设备 - 索尼/微软/任天堂主机'
    }
    
    return null;
}

// 产品中文解释
const productTranslations = {
    // 音频
    'Sony WH-1000XM5': '索尼 WH-1000XM5 - 顶级降噪无线耳机',
    'Apple AirPods Pro': '苹果 AirPods Pro 2 - 主动降噪无线耳塞',
    'Bose QuietComfort': 'Bose QuietComfort - 经典降噪耳机',
    'Bose QC45': 'Bose QC45 - 头戴式降噪耳机',
    'JBL speakers': 'JBL蓝牙音箱 - 便携音响',
    'Sonos soundbar': 'Sonos条形音箱 - 家庭影院音响',
    'Amazon Echo Dot': 'Amazon Echo Dot 5 - 智能音箱Alexa',
    'Sony WF-1000XM5': '索尼 WF-1000XM5 - 真无线降噪耳机',
    'Samsung Galaxy Buds': '三星 Galaxy Buds - 安卓无线耳机',
    'Shokz headphones': 'Shokz韶音 - 骨传导耳机',
    // 电脑配件
    'Logitech MX Master': '罗技 MX Master 3S - 办公鼠标',
    'Logitech G Pro Mouse': '罗技 G Pro - 电竞鼠标',
    'Dell Monitor': '戴尔 U2723QE - 4K专业显示器',
    'Samsung T7 SSD': '三星 T7 - 移动固态硬盘',
    'Laptop Stand': '笔记本铝合金支架 - 散热支架',
    'USB-C Hub': '雷电4/USB-C扩展坞 - 多端口扩展',
    'Mechanical Keyboard': '机械键盘 - 青轴/红轴',
    'Corsair Keyboard': '海盗船机械键盘 - 游戏键盘',
    'Keychron Keyboard': 'Keychron - 热门机械键盘',
    // 智能家居
    'Google Nest Hub': 'Google Nest Hub 2 - 智能显示屏',
    'Ring Video Doorbell': 'Ring 智能门铃 - 带摄像头',
    'Philips Hue': '飞利浦 Hue - 智能彩灯',
    'TP-Link Smart Plug': 'TP-Link 智能插座 - WiFi控制',
    'Nest Thermostat': 'Nest 智能恒温器 - 省电温控',
    'Eufy Robot Vacuum': 'Eufy 扫地机器人 - 性价比之选',
    'Wyze Camera': 'Wyze 智能摄像头 - 便宜好用',
    // 游戏设备
    'PlayStation 5': 'PS5 游戏机 - 索尼次世代主机',
    'Xbox Series X': 'Xbox Series X - 微软游戏主机',
    'Nintendo Switch': 'Nintendo Switch - 任天堂游戏机',
    'Razer Gaming Headset': 'Razer 北海巨妖 - 游戏耳机',
    'SteelSeries Headset': 'SteelSeries 赛睿 - 游戏耳机',
    'Xbox Elite Controller': 'Xbox Elite手柄 2代 - 专业手柄',
    // 健身
    'Apple Watch Ultra': 'Apple Watch Ultra 2 - 苹果顶级手表',
    'Fitbit Charge 6': 'Fitbit Charge 6 - 健身追踪器',
    'Garmin Forerunner': 'Garmin Forerunner - 专业跑步手表',
    'Peloton': 'Peloton - 健身课程订阅+设备',
    'Whoop Band': 'Whoop - 专业健身监测手环',
    'Oura Ring': 'Oura Ring - 睡眠监测戒指',
    // 摄影
    'Canon EOS R50': '佳能 EOS R50 - APS-C微单相机',
    'Sony A6700': '索尼 A6700 - APS-C微单旗舰',
    'DJI Osmo': 'DJI Osmo - 手持云台相机',
    'GoPro Hero 12': 'GoPro Hero 12 - 运动相机',
    'Elgato Camo': 'Elgato Camo - 直播摄像头软件',
    'DJI Mini': 'DJI Mini - 迷你无人机',
    'Insta360 X4': 'Insta360 X4 - 全景运动相机',
    // 生活
    'Nespresso Vertuo': 'Nespresso Vertuo - 胶囊咖啡机',
    'Instant Pot Pro': 'Instant Pot Pro - 多功能压力锅',
    'Dyson V15': 'Dyson V15 - 戴森最强吸尘器',
    'Philips Airfryer': '飞利浦空气炸锅 XXL',
    'iRobot Roomba': 'iRobot Roomba - 扫地机器人',
    'Vitamix Blender': 'Vitamix - 专业破壁搅拌机',
    'Ninja Blender': 'Ninja blender - 厨房搅拌机',
    // AI工具订阅
    'Claude Pro': 'Claude Pro - Anthropic AI助手订阅',
    'ChatGPT Plus': 'ChatGPT Plus - OpenAI订阅会员',
    'Midjourney': 'Midjourney - AI图像生成订阅',
    'GitHub Copilot': 'GitHub Copilot - AI编程助手订阅',
    'Notion AI': 'Notion AI - 笔记AI增强订阅',
    'Perplexity Pro': 'Perplexity Pro - AI搜索订阅',
    'Cursor Pro': 'Cursor Pro - AI代码编辑器订阅',
    'Gamma App': 'Gamma - AI演示文稿制作工具',
    // 网络安全
    'NordVPN': 'NordVPN - 优质VPN服务',
    '1Password': '1Password - 密码管理器',
    'YubiKey': 'YubiKey 5 - 硬件安全密钥',
    'LastPass': 'LastPass - 密码管理器',
    'Bitwarden': 'Bitwarden - 开源密码管理器',
    'Norton Security': 'Norton诺顿 - 杀毒安全软件',
    'ExpressVPN': 'ExpressVPN - VPN服务',
    // 教育
    'Udemy Courses': 'Udemy课程 - 各类在线课程',
    'Coursera Plus': 'Coursera Plus - 在线教育平台',
    'LinkedIn Learning': 'LinkedIn Learning - 职业学习平台',
    'Kindle Paperwhite': 'Kindle Paperwhite - 电子书阅读器',
    'Skillshare': 'Skillshare - 技能分享订阅',
    'MasterClass': 'MasterClass - 大师课',
    // 体育用品
    'NBA Jersey': 'NBA球衣 - 各球队官方球衣',
    'NFL Jersey': 'NFL球衣 - 橄榄球球衣',
    'Basketball': '篮球 - 室内外篮球',
    'Football': '橄榄球 - 美式足球',
    'Baseball Glove': '棒球手套 - 防守装备',
    'Soccer Ball': '足球 - 国际标准足球',
    'Tennis Racket': '网球拍 - 专业网球拍',
    'Golf Balls': '高尔夫球 - 品牌高尔夫球',
    'Golf Club': '高尔夫球杆套装',
    'Boxing Gloves': '拳击手套 - 训练比赛用',
    'Resistance Bands': '阻力带套装 - 健身弹力带',
    'Dumbbells': '哑铃 - 可调式哑铃组',
    'Kettlebell': '壶铃 - 健身壶铃',
    'Foam Roller': '泡沫轴 - 肌肉放松工具',
    'Sports Bag': '运动背包 - 健身包',
    'Jump Rope': '跳绳 - 速度训练跳绳',
    'Smartphone Sports Mount': '手机运动支架 - 健身时看教程',
    'Action Camera': '运动相机 - GoPro类',
    'GPS Sports Watch': 'GPS运动手表 - 跑步手表',
    'Hydration Pack': '运动水袋背包 - 跑步骑行'
};

// Category mapping based on keywords - EXPANDED
const categoryRules = [
    {
        category: '🎧 音频设备',
        keywords: ['headphone', 'earbud', 'speaker', 'audio', 'sound', 'music', 'podcast', 'airpod', 'beats', 'bose', 'sony headphones', 'noise cancelling', 'speaker', 'alexa', 'echo', 'siri', 'jbl', 'sonos', 'soundbar', 'shokz'],
        products: ['Sony WH-1000XM5', 'Apple AirPods Pro', 'Bose QuietComfort', 'JBL speakers', 'Sonos soundbar', 'Amazon Echo Dot', 'Sony WF-1000XM5', 'Shokz headphones']
    },
    {
        category: '📱 手机配件',
        keywords: ['iphone', 'samsung', 'galaxy', 'pixel', 'phone', 'android', 'apple', 'smartphone', 'mobile', 'oneplus', 'moto', 'lg'],
        products: ['iPhone 15 Pro Case', 'MagSafe Charger', 'Samsung Galaxy S24', 'Anker USB-C Cable', 'Spigen Screen Protector', 'Qi Wireless Charger']
    },
    {
        category: '💻 电脑配件',
        keywords: ['laptop', 'macbook', 'thinkpad', 'dell', 'hp', 'computer', 'pc', 'windows', 'chromebook', 'surface', 'asus', 'acer', 'razer', 'alienware'],
        products: ['Laptop Stand', 'USB-C Hub', 'Mechanical Keyboard', 'Logitech MX Master', 'Dell Monitor', 'Samsung T7 SSD']
    },
    {
        category: '🏠 智能家居',
        keywords: ['smart home', 'alexa', 'google home', 'nest', 'ring', 'smart plug', 'smart light', 'echo', 'homepod', 'automation', 'smart lock', 'camera', 'thermostat'],
        products: ['Amazon Echo Dot', 'Google Nest Hub', 'Ring Video Doorbell', 'Philips Hue', 'TP-Link Smart Plug', 'Nest Thermostat']
    },
    {
        category: '🎮 游戏设备',
        keywords: ['playstation', 'xbox', 'nintendo', 'gaming', 'gamer', 'ps5', 'steam deck', 'gaming chair', 'controller', 'switch', 'gaming mouse', 'gaming keyboard', 'fortnite', 'minecraft'],
        products: ['PlayStation 5', 'Xbox Series X', 'Nintendo Switch', 'Razer Gaming Headset', 'Logitech G Pro Mouse', 'Corsair Keyboard']
    },
    {
        category: '🏃 健康健身',
        keywords: ['fitness', 'workout', 'exercise', 'gym', 'running', 'yoga', 'health', 'fitbit', 'garmin', 'smartwatch', 'apple watch', 'weight loss', 'training', 'sports'],
        products: ['Apple Watch Ultra', 'Fitbit Charge 6', 'Garmin Forerunner', 'Peloton', 'Yoga Mat', 'Resistance Bands', 'Foam Roller']
    },
    {
        category: '📸 摄影摄像',
        keywords: ['camera', 'canon', 'nikon', 'sony camera', 'gimbal', 'drone', 'youtube', 'content creator', 'streaming', 'video', 'photo', 'cinematic', 'goPro', 'insta360'],
        products: ['Canon EOS R50', 'Sony A6700', 'DJI Osmo', 'GoPro Hero 12', 'Elgato Camo', 'Ring Light', 'Microphone']
    },
    {
        category: '☕ 生活品质',
        keywords: ['coffee', 'espresso', 'air fryer', 'instant pot', 'robot vacuum', 'dyson', 'kitchen', 'cooking', 'cleaning', 'vacuum', 'tea', 'blender', 'juice'],
        products: ['Nespresso Vertuo', 'Instant Pot Pro', 'Dyson V15', 'Philips Airfryer', 'iRobot Roomba', 'Vitamix Blender']
    },
    {
        category: '🤖 AI/科技产品',
        keywords: ['ai', 'chatgpt', 'gpt', 'llm', 'artificial intelligence', 'copilot', 'gemini', 'claude', 'openai', 'anthropic', 'midjourney', 'stable diffusion', 'tech', 'software', 'app'],
        products: ['AI Tool Subscriptions', 'Anthropic Claude Pro', 'ChatGPT Plus', 'Midjourney', 'GitHub Copilot', 'Notion AI', 'Perplexity Pro']
    },
    {
        category: '🔐 网络安全',
        keywords: ['vpn', 'password', 'security', 'privacy', 'hack', 'breach', 'malware', 'encryption', 'cyber', 'antivirus', 'firewall'],
        products: ['NordVPN', '1Password', 'YubiKey', 'LastPass', 'Bitwarden', 'Norton Security']
    },
    {
        category: '📚 教育培训',
        keywords: ['course', 'Udemy', 'Coursera', 'skill', 'learning', 'certificate', 'degree', 'education', 'training', 'book', 'kindle', 'reading', 'study'],
        products: ['Udemy Courses', 'Coursera Plus', 'LinkedIn Learning', 'Kindle Paperwhite', 'Skillshare', 'MasterClass']
    },
    {
        category: '🧸 玩具游戏',
        keywords: ['toy', 'game', 'lego', 'kids', 'children', 'board game', 'puzzle', 'play', 'baby', 'gift', 'present', 'birthday'],
        products: ['LEGO Sets', 'Board Games', 'Play-Doh', 'Nerf Blaster', 'Melissa & Doug', 'Video Games']
    },
    {
        category: '💄 美妆护肤',
        keywords: ['beauty', 'skincare', 'makeup', 'cosmetic', 'skin', 'hair', 'nail', 'perfume', 'fragrance', 'wellness'],
        products: ['Face Moisturizer', 'Vitamin C Serum', 'Makeup Palette', 'Hair Dryer', 'Nail Kit', 'Perfume']
    },
    {
        category: '👗 时尚服饰',
        keywords: ['fashion', 'clothing', 'shoes', 'sneakers', 'jordan', 'nike', 'adidas', 'hoodie', 'jacket', 'watch', 'sunglasses', 'bag'],
        products: ['Nike Sneakers', 'Adidas Hoodie', 'Casio Watch', 'Ray-Ban Sunglasses', 'Levi\'s Jeans', 'North Face Jacket']
    },
    {
        category: '🏕️ 户外运动',
        keywords: ['camping', 'hiking', 'outdoor', 'fishing', 'biking', 'cycling', 'climbing', 'tent', 'backpack'],
        products: ['Camping Tent', 'Hiking Backpack', 'Portable Power Station', 'Solar Charger', 'Fishing Rod', 'Bike Helmet']
    },
    {
        category: '🏆 体育赛事及用品',
        keywords: [
            // General sports
            'sports', 'nba', 'nfl', 'mlb', 'nhl', 'marching band', 'super bowl', 'world series', 'finals',
            // Specific sports
            'basketball', 'football', 'baseball', 'soccer', 'tennis', 'golf', 'boxing', 'ufc', 'mma', 'wwe', 'wrestling',
            'volleyball', 'swimming', 'track and field', 'marathon', 'triathlon', 'skiing', 'snowboarding', 'surfing',
            // Teams
            'lakers', 'warriors', 'celtics', 'yankees', 'dodgers', 'cowboys', 'eagles', 'chiefs', 'packers',
            'manchester united', 'liverpool', 'real madrid', 'barcelona', 'psg', 'bayern',
            // Events
            'march madness', 'olympics', 'world cup', 'stanley cup', 'nba finals', 'nfl playoffs',
            'us open', 'wimbledon', 'masters', 'indy 500', 'daytona 500',
            // Athletes
            'lebron', 'jordan', 'messi', 'ronaldo', 'mahomes', 'shohei ohtani', 'simone biles',
            // Gear
            'sports gear', 'sports equipment', 'jersey', 'trading cards', 'sports memorabilia',
            'sports betting', 'fantasy sports', 'draft kings', 'fanduel'
        ],
        products: [
            // Team Jerseys & Apparel
            'NBA Jersey', 'NFL Jersey', 'MLB Jersey', 'Soccer Jersey', 'Custom Jersey',
            // Sports Equipment
            'Basketball', 'Football', 'Baseball Glove', 'Soccer Ball', 'Tennis Racket', 'Golf Balls',
            'Golf Club', 'Boxing Gloves', 'MMA Gloves', 'Jump Rope', 'Weight Set',
            // Fitness & Training
            'Resistance Bands', 'Dumbbells', 'Pull-Up Bar', 'Kettlebell', 'Medicine Ball',
            'Foam Roller', 'Sports Bag', 'Gym Bag', 'Athletic Shorts', 'Sports Compression Wear',
            // Outdoor Sports
            'Bike', 'Skateboard', 'Surfboard', 'Snowboard', 'Ski Gear', 'Kayak', 'Paddleboard',
            // Fan Gear
            'Team Cap', 'Team Hoodie', 'Sports Jackets', 'Tailgate Gear', 'Stadium Seat Cushion',
            'Portable Chair', 'Cooler', 'Team Flag', 'Car Flag',
            // Tech & Accessories
            'Smartphone Sports Mount', 'Action Camera', 'GoPro', 'Sports Headphones', 'GPS Sports Watch',
            'Heart Rate Monitor', 'Fitness Tracker', 'Hydration Pack', 'Sports Water Bottle',
            // Recovery & Nutrition
            'Massage Gun', 'Ice Bath Tub', 'Compression Boots', 'Protein Powder', 'Energy Drinks',
            'Pre-Workout', 'Sports Drinks', 'Electrolyte Packets',
            // Trending Items
            'Taylor Swift Era Tour Merch', 'FIFA World Cup Gear', 'Olympics Merchandise',
            'March Madness Bracket Pool Supplies', 'Super Bowl Party Supplies'
        ]
    },
    {
        category: '🚗 汽车配件',
        keywords: ['car', 'auto', 'vehicle', 'driving', 'dash cam', 'tire', 'oil', 'tesla', 'electric vehicle', 'ev', 'charger'],
        products: ['Dash Cam', 'Car Phone Mount', 'Tesla Accessories', 'Jump Starter', 'Car Vacuum', 'Tire Pressure Gauge']
    }
];

// Map ALL trends to product opportunities
function mapTrendsToProducts(trends) {
    const opportunities = [];
    const filteredOut = [];
    
    for (const trend of trends) {
        // Check if trend should be excluded based on user preferences
        if (shouldExclude(trend.title)) {
            filteredOut.push({
                trend: trend.title,
                reason: '❌ 已过滤 - 不符合用户兴趣'
            });
            continue;
        }
        
        const trendText = `${trend.title} ${trend.newsItems.map(n => n.title + ' ' + n.snippet).join(' ')}`.toLowerCase();
        
        // Get background context for this trend
        const background = getTrendBackground(trend.title) || getTrendBackground(trendText);
        
        // Find matching categories
        let matched = false;
        for (const rule of categoryRules) {
            for (const keyword of rule.keywords) {
                if (trendText.includes(keyword)) {
                    opportunities.push({
                        trend: trend.title,
                        traffic: trend.traffic,
                        category: rule.category,
                        products: rule.products,
                        matchedKeyword: keyword,
                        news: trend.newsItems[0]?.title || '',
                        background: background,
                        isUserInterested: ['🤖 AI/科技产品', '💻 电脑配件', '🎧 音频设备', '📸 摄影摄像', '🔐 网络安全'].includes(rule.category)
                    });
                    matched = true;
                    break;
                }
            }
            if (matched) break;
        }
        
        // If no specific match, create a general opportunity based on trend title
        if (!matched && trend.title.length > 3 && !trend.title.match(/^[\w\s]{2,3}$/)) {
            opportunities.push({
                trend: trend.title,
                traffic: trend.traffic,
                category: '🔍 通用产品',
                products: ['Amazon Bestsellers', 'Top Rated Products', 'Trending Items', 'Gift Ideas', 'Popular Products'],
                matchedKeyword: 'general',
                news: trend.newsItems[0]?.title || '',
                background: background
            });
        }
    }
    
    return { opportunities, filteredOut };
}

// Score opportunities by affiliate potential
function scoreOpportunities(opportunities) {
    const scored = opportunities.map(opp => {
        let score = 50; // Base score
        
        // Higher traffic = higher score
        if (opp.traffic) {
            const num = parseInt(opp.traffic.replace(/[^0-9]/g, ''));
            if (opp.traffic.includes('+')) {
                if (num >= 200000) score += 40;
                else if (num >= 100000) score += 30;
                else if (num >= 50000) score += 20;
                else if (num >= 10000) score += 10;
            }
        }
        
        // Higher-value categories - David's interests
        if (['🤖 AI/科技产品', '💻 电脑配件', '🎧 音频设备', '📸 摄影摄像', '🔐 网络安全'].includes(opp.category)) {
            score += 25; // Boost for user's interests
        }
        
        // User explicitly interested
        if (opp.isUserInterested) {
            score += 15;
        }
        
        // Has good background context
        if (opp.background && !opp.background.includes('❌')) {
            score += 10;
        }
        
        // Seasonal awareness
        const month = new Date().getMonth();
        if (month === 10 || month === 11) {
            if (['🧸 玩具游戏', '👗 时尚服饰', '☕ 生活品质'].includes(opp.category)) {
                score += 20;
            }
        }
        
        return { ...opp, score };
    });
    
    scored.sort((a, b) => b.score - a.score);
    return scored;
}

// 翻译趋势词 - 带搜索意图分析
function translateTrend(trendText) {
    const lower = trendText.toLowerCase();
    
    // 先精确匹配
    for (const [keyword, translation] of Object.entries(trendTranslations)) {
        if (lower.includes(keyword)) {
            return translation;
        }
    }
    
    // 未知趋势词，返回null，让调用方决定如何显示
    return null;
}

// 获取趋势的中文解释或搜索链接
function getTrendExplanation(trendText) {
    const cn = translateTrend(trendText);
    if (cn) return cn;
    
    // 未知趋势词，生成简洁的Google搜索提示
    const encoded = encodeURIComponent(trendText);
    return `[Google搜索了解](https://www.google.com/search?q=${encoded}&hl=en)`;
}

// 获取趋势的搜索意图
function getSearchIntent(trendText) {
    const lower = trendText.toLowerCase();
    
    // 交易型搜索 - 购买意图
    const transactional = [
        'buy', 'price', 'deal', 'discount', 'coupon', 'sale', 'amazon', 
        'best', 'top', 'review', 'comparison', 'vs', 'versus', 'alternative',
        'cheap', 'affordable', 'budget', 'free', 'trial'
    ];
    
    // 信息型搜索 - 了解意图
    const informational = [
        'what is', 'how to', 'why', 'meaning', 'definition', 'explain',
        'difference between', 'vs', 'tutorial', 'guide', 'tips', 'ways',
        'news', 'update', 'release', 'announcement', 'announces'
    ];
    
    // 品牌型搜索
    const brand = [
        'apple', 'samsung', 'google', 'microsoft', 'amazon', 'nvidia', 
        'intel', 'amd', 'sony', 'lg', 'dyson', 'bose', 'jbl'
    ];
    
    // 产品型搜索
    const product = [
        'iphone', 'ipad', 'macbook', 'airpods', 'watch', 'galaxy', 
        'pixel', 'surface', 'echo', 'nest', 'ps5', 'xbox', 'switch'
    ];
    
    let intent = '🔍 信息型 - 了解/研究';
    let detail = '';
    
    // 检测搜索意图
    for (const t of transactional) {
        if (lower.includes(t)) {
            intent = '🛒 交易型 - 购买/比价';
            break;
        }
    }
    
    if (!informational.every(i => !lower.includes(i))) {
        intent = '📚 信息型 - 教程/指南';
    }
    
    // 检测品牌
    const foundBrands = brand.filter(b => lower.includes(b));
    if (foundBrands.length > 0) {
        detail += `品牌: ${foundBrands.join(', ')} | `;
    }
    
    // 检测产品类别
    const foundProducts = product.filter(p => lower.includes(p));
    if (foundProducts.length > 0) {
        detail += `产品: ${foundProducts.join(', ')}`;
    }
    
    if (detail) {
        return `${intent} | ${detail}`;
    }
    return intent;
}

// 翻译产品
function translateProduct(productName) {
    return productTranslations[productName] || null;
}

// Format report - 中英双语版
function formatReport(trends, opportunities, filteredOut) {
    const dateStr = new Date().toLocaleDateString('zh-CN', { 
        timeZone: 'Asia/Shanghai',
        year: 'numeric', month: '2-digit', day: '2-digit'
    });
    
    let msg = `🛒 **每日亚马逊产品机会简报** - ${dateStr}
📊 基于 Google Trends | ⭐=用户兴趣领域

`;
    
    // Group opportunities by category
    const byCategory = {};
    for (const opp of opportunities) {
        if (!byCategory[opp.category]) byCategory[opp.category] = [];
        byCategory[opp.category].push(opp);
    }
    
    // Summary stats
    msg += `📈 **趋势概况**
• 热门趋势: ${trends.length}个
• 匹配产品: ${opportunities.length}个
• 覆盖品类: ${Object.keys(byCategory).length}个
`;
    if (filteredOut && filteredOut.length > 0) {
        msg += `• 已过滤(体育/娱乐): ${filteredOut.length}个
`;
    }
    msg += `
`;
    
    // Show filtered trends
    if (filteredOut && filteredOut.length > 0) {
        msg += `🚫 **已过滤趋势** (体育/娱乐/名人)
`;
        msg += `━━━━━━━━━━━━━━━━━━━━
`;
        for (const f of filteredOut.slice(0, 5)) {
            msg += `• ${f.trend} - ${f.reason}
`;
        }
        if (filteredOut.length > 5) {
            msg += `... 还有${filteredOut.length - 5}个
`;
        }
        msg += `
`;
    }
    
    // Hot trends with context
    if (opportunities.length > 0) {
        msg += `🔥 **今日趋势 TOP 10 (中英对照+背景)**
`;
        msg += `━━━━━━━━━━━━━━━━━━━━
`;
        
        const topTrends = opportunities.slice(0, 10);
        for (let i = 0; i < topTrends.length; i++) {
            const o = topTrends[i];
            const cn = translateTrend(o.trend);
            const intent = getSearchIntent(o.trend);
            const background = o.background || (cn ? cn : '📖 需搜索了解');
            
            const interestMarker = o.isUserInterested ? ' ⭐' : '';
            
            msg += `${i + 1}. 【${o.trend}】${interestMarker}
`;
            msg += `   📖 背景: ${background}
`;
            msg += `   🎯 意图: ${intent}
`;
            if (o.traffic) msg += `   📊 热度: ${o.traffic}
`;
            if (o.products && o.products[0]) {
                const cnProduct = translateProduct(o.products[0]);
                msg += `   📦 推荐: ${o.products[0]}${cnProduct ? ` (${cnProduct})` : ''}
`;
            }
            msg += `
`;
        }
    }
    
    // User-interested categories first
    const userInterestedCategories = ['🤖 AI/科技产品', '💻 电脑配件', '🎧 音频设备', '📸 摄影摄像', '🔐 网络安全', '🏠 智能家居'];
    const sortedCategories = Object.entries(byCategory).sort((a, b) => {
        const aInterested = userInterestedCategories.includes(a[0]);
        const bInterested = userInterestedCategories.includes(b[0]);
        if (aInterested && !bInterested) return -1;
        if (!aInterested && bInterested) return 1;
        return b[1].length - a[1].length;
    });
    
    if (sortedCategories.length > 0) {
        msg += `⭐ **重点推荐 (用户兴趣优先)**
`;
        msg += `━━━━━━━━━━━━━━━━━━━━
`;
        
        let rank = 1;
        for (const [category, opps] of sortedCategories) {
            if (rank > 6) break;
            
            const isUserInterested = userInterestedCategories.includes(category);
            const marker = isUserInterested ? ' ⭐' : '';
            
            msg += `${rank}. ${category}${marker}
`;
            
            const uniqueProducts = [...new Set(opps.flatMap(o => o.products))].slice(0, 3);
            for (const product of uniqueProducts) {
                const cnProduct = translateProduct(product);
                msg += `   • ${product}
`;
                if (cnProduct) msg += `     ${cnProduct}
`;
            }
            
            const topOpp = opps[0];
            if (topOpp && topOpp.trend) {
                const cnTrend = translateTrend(topOpp.trend);
                const background = topOpp.background || (cnTrend ? cnTrend : '需搜索');
                msg += `   📈 趋势: ${topOpp.trend}
`;
                msg += `   ${background}
`;
            }
            
            msg += `
`;
            rank++;
        }
    }
    
    // Action items
    msg += `💡 **行动建议**
━━━━━━━━━━━━━━━━━━━━
• ⭐ = 符合你的兴趣(AI/科技/硬件)
• **内容创作**: 针对⭐趋势写评测/对比文章
• **联盟营销**: 优先推广⭐推荐产品

---
🕐 ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
📡 Google Trends + AI产品映射 | ❌已过滤体育/娱乐/名人
`;
    
    return msg;
}

async function main() {
    log('=== Amazon Opportunities Analysis Started ===');
    
    mkdirSync(`${WORKDIR}/logs`, { recursive: true });
    
    // Step 1: Fetch ALL Google Trends (no filtering)
    log('Fetching all Google Trends...');
    const trends = await fetchTrends();
    
    // Step 2: Map ALL trends to product opportunities (with filtering)
    log('Analyzing trends for product opportunities...');
    const { opportunities, filteredOut } = mapTrendsToProducts(trends);
    const scoredOpportunities = scoreOpportunities(opportunities);
    
    // Step 3: Generate report with better context
    const report = formatReport(trends, scoredOpportunities, filteredOut);
    
    // Save outputs
    const mdFile = `${WORKDIR}/logs/amazon_opportunities_latest.md`;
    const txtFile = `${WORKDIR}/logs/amazon_to_send.txt`;
    writeFileSync(mdFile, report);
    writeFileSync(txtFile, report);
    
    console.log('MESSAGE_START');
    console.log(report);
    console.log('MESSAGE_END');
    
    log(`=== Analysis Complete: ${opportunities.length} opportunities found ===`);
}

main().catch(err => {
    log(`Fatal error: ${err.message}`);
    process.exit(1);
});
