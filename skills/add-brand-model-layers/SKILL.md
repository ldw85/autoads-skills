name: add-brand-model-layers
description: 为存量广告系列添加Brand_Model精细化分层广告组(L0 $3-$7)
trigger: natural language trigger
usage: "给xxx广告系列添加Brand_Model分层"
  "给Campaign 23738239843添加Brand_Model层"
  "为Betta广告系列添加精细化分层"
examples:
  - "给 yeahpromos 账号的 Betta_SE_Pool_Cleaner_US (1775622886) 添加Brand_Model分层"
  - "给存量广告系列添加5个Brand_Model广告组"
parameters:
  - campaign-id: Campaign ID (必需)
  - customer-id: Customer ID (必需)
  - brand: 品牌名
  - keywords: 逗号分隔的关键词
  - cap-bid: 存量广告组最大CPC