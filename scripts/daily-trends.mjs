/**
 * Daily Google Trends + Opportunity Analysis
 * Fetches US Google Trends, AI-filters content, analyzes Amazon opportunities
 */

import { writeFileSync, mkdirSync } from 'fs';

const WORKDIR = '/root/.openclaw/workspace';
const LOG_FILE = `${WORKDIR}/logs/daily-trends.log`;

function log(msg) {
    const timestamp = new Date().toISOString();
    const line = `[${timestamp}] ${msg}\n`;
    try {
        writeFileSync(LOG_FILE, line, { flag: 'a' });
    } catch (e) {}
    console.log(msg);
}

function decodeHtmlEntities(text) {
    return text
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ')
        .replace(/&apos;/g, "'");
}

// Fetch Google Trends RSS
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
            const picSourceMatch = /<ht:picture_source>(.*?)<\/ht:picture_source>/i.exec(itemXml);
            const trafficMatch = /<ht:approx_traffic>(.*?)<\/ht:approx_traffic>/i.exec(itemXml);
            
            const title = titleMatch ? decodeHtmlEntities(titleMatch[1]) : '';
            const picSource = picSourceMatch ? decodeHtmlEntities(picSourceMatch[1]) : '';
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
            
            items.push({ title, picSource, traffic, newsItems });
        }
        
        log(`Fetched ${items.length} trend items`);
        return items;
        
    } catch (error) {
        log(`Error fetching trends: ${error.message}`);
        return [];
    }
}

// Filter trends for relevant content
function filterTrends(items) {
    const excludeSources = [
        /espn|yahoo sports|bleacher report|sports illustrated|fox sports|cbs sports|bbc sport|skysports/i,
        /yahoo\b|ahoo\b|msn sports|cnbc sports/i,
        /wwe|ufc|boxing|mma|martial arts/i,
        /celebrity|tmz|people|daily mail|star magazine|us weekly|radar online/i,
        /florida gators|georgia bulldogs|alabama crimson|tamu|ohio state|texas longhorns|michigan wolfs/i,
        /beale street bears|memphis grizzlies|college sports|college basketball|college football/i,
        /cleveland\.com|detroit free press|mlive\.com|espn\b|247sports|sports.yahoo/i,
        /pvamu home|furman university/i,
        /free press|mlive|cincinnati|enquirer|ohio\.com/i,
    ];
    
    const excludeTitlePatterns = [
        /\b(dodgers|padres|yankees|cubs|red sox|celtics|lakers|warriors|nba|nfl|mlb|nhl|ufa|fantasy\b|playoff|championship|tournament|game (chat|recap|score|start)|live stream|spring training)\b/i,
        /\b(wwe|wrestlemania|raw|smackdown| Dynamite|pro wrestling|aew)\b/i,
        /\b(march madness|ncaa tournament|bracket|poll|college basketball|final four)\b/i,
        /\b(celebrity|star|scandal|divorce|breakup|rumor|gossip|affair|michael movie)\b/i,
        /\b(movie premiere|album release|song debut|trailer drop|box office|tv show|series|film)\b/i,
        /\b(horoscopes|horoscope|zodiac|astrology)\b/i,
        /\b(vs |versus)\b/i,
        /\b(championship|finals?|semifinals?|bracket|schedule|picks?|odds|predictions|bets|injury)\b/i,
        /\b(hbo|netflix|disney|hulu|prime video|paramount|spotify)\b/i,
        /\b(basketball\b|football\b|baseball\b|soccer\b|tennis\b|golf\b|hockey\b|wrestling)\b/i,
    ];
    
    const keepPatterns = [
        /\b(ai|artificial intelligence|llm|gpt|gemini|claude|chatgpt|openai|anthropic|deepmind|copilot|midjourney|stable diffusion)\b/i,
        /\b(apple|google\b|meta|microsoft|amazon|tesla|nvidia|amd|intel|qualcomm|samsung|sony)\b/i,
        /\b(iphone|macbook|ipad|pixel|galaxy|macbook|airpods|surface|thinkpad)\b/i,
        /\b(chip|processor|cpu|gpu|ram|ssd|storage|battery|screen|display)\b/i,
        /\b(launch|release|announce|unveil|reveal|announcement|event|keynote|countdown)\b/i,
        /\b(review|benchmark|test|compare|comparison|unboxing)\b/i,
        /\b(security|privacy|breach|hack|vulnerability|malware|ransomware|cyber|password)\b/i,
        /\b(app|update|ios|android|windows|macos|linux|software)\b/i,
        /\b(github|coding|programming|developer|api|sdk|framework|python|javascript|rust)\b/i,
        /\b(startup|funding|series|valuation|ipo|acquisition|merger|ceo|founder|venture)\b/i,
        /\b(robotics|drone|vr ar|virtual reality|augmented reality|metaverse)\b/i,
        /\b(smart home|iot|automation|assistant|alexa|siri|google assistant)\b/i,
    ];
    
    const filtered = [];
    
    for (const item of items) {
        const mainText = item.title.toLowerCase();
        const allNewsText = item.newsItems.map(n => `${n.title} ${n.source} ${n.snippet}`).join(' ').toLowerCase();
        const fullText = `${mainText} ${allNewsText}`;
        
        let hasExcludedSource = false;
        for (const pattern of excludeSources) {
            if (pattern.test(item.picSource)) { hasExcludedSource = true; break; }
        }
        
        let hasExcludedTitle = false;
        for (const pattern of excludeTitlePatterns) {
            if (pattern.test(mainText)) { hasExcludedTitle = true; break; }
        }
        
        let shouldKeep = false;
        for (const pattern of keepPatterns) {
            if (pattern.test(fullText)) { shouldKeep = true; break; }
        }
        
        const isExcluded = (hasExcludedSource || hasExcludedTitle) && !shouldKeep;
        if (isExcluded) { log(`Filtered: "${item.title}"`); continue; }
        if (item.newsItems.length === 0) continue;
        
        filtered.push(item);
    }
    
    log(`Filtered ${items.length} → ${filtered.length} relevant items`);
    return filtered;
}

// Analyze opportunities from filtered trends
function analyzeOpportunities(items) {
    const opportunities = [];
    
    // Must match BOTH a trend keyword AND have valid products
    // Format: { trigger: [keywords that trigger this category], products: [...] }
    const categoryMapping = [
        {
            category: '🤖 AI/科技产品',
            triggers: ['ai', 'chatgpt', 'llm', 'gpt', 'gemini', 'claude', 'openai', 'anthropic', 'midjourney', 'stable diffusion', 'copilot'],
            products: ['AI工具订阅', 'Anthropic Claude Pro', 'ChatGPT Plus', 'AI耳机', 'AI鼠标']
        },
        {
            category: '📱 消费电子',
            triggers: ['iphone', 'ipad', 'macbook', 'pixel', 'galaxy', 'samsung', 'apple', 'oneplus', 'sony', 'kindle'],
            products: ['手机配件', '平板保护套', '无线充电器', '蓝牙耳机', '屏幕保护膜']
        },
        {
            category: '🏠 智能家居',
            triggers: ['smart home', 'alexa', 'google home', 'homepod', 'smart speaker', 'smart plug', 'smart lock', 'nest', 'ring'],
            products: ['智能音箱', '智能插座', '智能门锁', '监控摄像头', '智能灯泡']
        },
        {
            category: '💻 生产力工具',
            triggers: ['laptop', 'monitor', 'webcam', 'standing desk', 'laptop stand', 'mechanical keyboard', 'ergonomic'],
            products: ['笔记本支架', '机械键盘', '人体工学鼠标', '4K显示器', 'USB-C Hub']
        },
        {
            category: '🔐 网络安全',
            triggers: ['vpn', 'password manager', 'security key', 'privacy', 'encryption', 'malware', 'phishing', 'hack'],
            products: ['VPN服务', '密码管理器', 'YubiKey', '隐私屏幕', '杀毒软件']
        },
        {
            category: '🎮 游戏设备',
            triggers: ['playstation', 'xbox', 'nintendo', 'steam deck', 'gaming', 'gamer', 'esports'],
            products: ['游戏耳机', '游戏鼠标', '手柄', '游戏键盘', '显示器支架']
        },
        {
            category: '🏃 健康健身',
            triggers: ['fitness tracker', 'smartwatch', 'fitbit', 'garmin', 'whoop', 'workout', 'exercise'],
            products: ['智能手表', '健身手环', '运动耳机', '瑜伽垫', '阻力带']
        },
        {
            category: '🎧 音频设备',
            triggers: ['headphones', 'earbuds', 'airpods', 'speaker', 'sonos', 'bose', 'audio', 'noise canceling'],
            products: ['无线耳机', '降噪耳机', '蓝牙音箱', '声卡', '麦克风']
        },
        {
            category: '📸 摄影摄像',
            triggers: ['camera', 'canon', 'nikon', 'sony camera', 'gimbal', 'drone', 'youtube creator', 'content creator'],
            products: ['相机三脚架', '补光灯', '麦克风', '稳定器', '无人机']
        },
        {
            category: '☕ 生活品质',
            triggers: ['coffee', 'espresso', 'air fryer', 'instant pot', 'robot vacuum', 'dyson'],
            products: ['咖啡机', '空气炸锅', '扫地机器人', '吸尘器', '厨房小家电']
        }
    ];
    
    // Keywords that indicate sports/entertainment - should NOT generate opportunities
    const excludeKeywords = [
        'basketball', 'football', 'baseball', 'soccer', 'tennis', 'golf', 'hockey',
        'march madness', 'ncaa', 'playoff', 'championship', 'tournament',
        'wwe', 'ufc', 'boxing', 'mma', 'wrestling',
        'movie', 'film', 'netflix', 'hbo', 'disney', 'series', 'episode',
        'celebrity', 'divorce', 'scandal', 'gossip'
    ];
    
    for (const item of items) {
        const fullText = `${item.title} ${item.newsItems.map(n => n.title).join(' ')}`.toLowerCase();
        
        // Skip if it's sports/entertainment
        let shouldSkip = false;
        for (const ex of excludeKeywords) {
            if (fullText.includes(ex)) {
                shouldSkip = true;
                break;
            }
        }
        if (shouldSkip) continue;
        
        // Find matching categories
        for (const cat of categoryMapping) {
            for (const trigger of cat.triggers) {
                // Use word boundary matching for better accuracy
                const regex = new RegExp(`\\b${trigger}\\b`, 'i');
                if (regex.test(fullText)) {
                    opportunities.push({
                        trend: item.title,
                        category: cat.category,
                        matched: trigger,
                        traffic: item.traffic,
                        products: cat.products,
                        news: item.newsItems[0]?.title || ''
                    });
                    break; // Only match one category per item
                }
            }
        }
    }
    
    return opportunities;
}

// Format opportunities for display
function formatOpportunities(opportunities, filteredItems) {
    if (opportunities.length === 0 && filteredItems.length === 0) {
        return '';
    }
    
    let msg = '';
    
    if (filteredItems.length > 0) {
        msg += '\n\n---\n';
        msg += '## 🔍 商机分析\n';
        
        // Group opportunities by category
        const byCategory = {};
        for (const opp of opportunities) {
            if (!byCategory[opp.category]) {
                byCategory[opp.category] = [];
            }
            byCategory[opp.category].push(opp);
        }
        
        if (opportunities.length > 0) {
            for (const [category, opps] of Object.entries(byCategory)) {
                msg += `\n### ${category}\n`;
                
                for (const opp of opps) {
                    msg += `**🔥 ${opp.trend}**`;
                    if (opp.traffic) msg += ` (${opp.traffic} 搜索)`;
                    msg += '\n';
                    if (opp.news) {
                        msg += `> ${opp.news.substring(0, 100)}${opp.news.length > 100 ? '...' : ''}\n`;
                    }
                    msg += `🛒 **亚马逊选品:** ${opp.products.join(' | ')}\n`;
                }
            }
            
            msg += '\n**💡 亚马逊机会提示**\n';
            msg += '- 热门趋势相关产品可考虑联盟营销\n';
            msg += '- 高流量关键词适合做 SEO 内容\n';
            msg += '- 产品评测类文章转化率较高\n';
        } else {
            msg += '\n今日趋势与科技/商业关联度较低，商机有限。\n';
            msg += '💡 工作日通常有更多 AI/科技 相关趋势\n';
        }
    }
    
    return msg;
}

// Format trends message
function formatMessage(items, dateStr, opportunities) {
    let msg = `📈 **每日趋势简报** - ${dateStr}\n`;
    msg += `筛选了 ${items.length} 条相关内容\n`;
    
    if (items.length > 0) {
        const categories = {
            '🤖 AI/科技': [],
            '📱 产品/硬件': [],
            '💼 商业/创业': [],
            '🔐 安全/隐私': [],
            '📰 其他科技': []
        };
        
        for (const item of items) {
            const text = `${item.title} ${item.newsItems.map(n => n.title + ' ' + n.source).join(' ')}`.toLowerCase();
            
            if (/\b(ai|artificial intelligence|llm|gpt|gemini|claude|chatgpt|openai|anthropic|deepmind|copilot|midjourney)\b/i.test(text)) {
                categories['🤖 AI/科技'].push(item);
            } else if (/\b(iphone|macbook|ipad|pixel|galaxy|mac|airpods|watch|apple|google phone|samsung|oneplus|laptop|computer)\b/i.test(text)) {
                categories['📱 产品/硬件'].push(item);
            } else if (/\b(startup|funding|series|valuation|ipo|acquisition|merger|ceo|founder|venture|business)\b/i.test(text)) {
                categories['💼 商业/创业'].push(item);
            } else if (/\b(security|privacy|breach|hack|vulnerability|malware|ransomware|cyber|password)\b/i.test(text)) {
                categories['🔐 安全/隐私'].push(item);
            } else {
                categories['📰 其他科技'].push(item);
            }
        }
        
        for (const [cat, catItems] of Object.entries(categories)) {
            if (catItems.length > 0) {
                msg += `\n${cat}\n`;
                for (const item of catItems.slice(0, 5)) {
                    msg += `• ${item.title}`;
                    if (item.traffic) msg += ` (${item.traffic})`;
                    msg += '\n';
                    if (item.newsItems.length > 0) {
                        const top = item.newsItems[0];
                        if (top.title && top.title !== item.title) {
                            const truncated = top.title.length > 60 ? top.title.substring(0, 60) + '...' : top.title;
                            msg += `  → ${truncated}\n`;
                        }
                    }
                }
                if (catItems.length > 5) {
                    msg += `  +${catItems.length - 5} more\n`;
                }
            }
        }
    } else {
        msg += '\n今日暂无符合您兴趣的科技/AI趋势热点。\n';
        msg += '💡 提示：工作日通常有更多科技/商业相关内容\n';
    }
    
    msg += '\n---\n💡 过滤掉了娱乐/体育/政治内容';
    msg += formatOpportunities(opportunities, items);
    msg += `\n\n🕐 ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`;
    
    return msg;
}

async function main() {
    const dateStr = new Date().toLocaleDateString('zh-CN', { 
        timeZone: 'Asia/Shanghai',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).replace(/\//g, '-');
    
    log('=== Daily Trends Briefing Started ===');
    
    mkdirSync(`${WORKDIR}/logs`, { recursive: true });
    mkdirSync(`${WORKDIR}/scripts`, { recursive: true });
    
    const items = await fetchTrends();
    if (items.length === 0) {
        log('No trends fetched');
        process.exit(0);
    }
    
    const filtered = filterTrends(items);
    const opportunities = analyzeOpportunities(filtered);
    const message = formatMessage(filtered, dateStr, opportunities);
    
    writeFileSync(`${WORKDIR}/logs/trends_latest.md`, message);
    
    console.log('MESSAGE_START');
    console.log(message);
    console.log('MESSAGE_END');
    
    log('=== Daily Trends Briefing Complete ===');
}

main().catch(err => {
    log(`Fatal error: ${err.message}`);
    process.exit(1);
});
