qiyun_xiuxian/
├── client/                      # 客户端代码
│   ├── main.py                  # 客户端主程序入口
│   ├── assets/                  # 资源文件
│   │   ├── icons/               # 图标 (托盘、按钮等)
│   │   ├── images/              # 背景、装备、物品图片
│   │   └── styles/              # QSS 样式表文件
│   ├── ui/                      # PyQt界面文件 (由.ui文件生成或手写)
│   │   ├── login_window.py      # 登录/注册窗口
│   │   ├── main_window.py       # 主界面 (QQ风格)
│   │   ├── widgets/             # 可复用的小控件
│   │   │   ├── character_info_widget.py # 顶部角色信息面板
│   │   │   ├── chat_widget.py         # 聊天室控件
│   │   │   └── cultivation_log_widget.py # 修炼日志控件
│   │   └── windows/             # 各功能模块弹出的独立窗口
│   │       ├── backpack_window.py
│   │       ├── cave_window.py
│   │       ├── shop_window.py
│   │       └── ...
│   ├── network/                 # 网络通信模块
│   │   ├── api_client.py        # 封装HTTP请求 (登录、买东西等)
│   │   └── websocket_client.py  # 封装WebSocket实时通信
│   └── state_manager.py         # 客户端状态管理器 (保存玩家数据、token等)
│
├── server/                      # 服务端代码
│   ├── main.py                  # 服务端主程序入口 (启动FastAPI)
│   ├── api/                     # API路由/接口定义
│   │   ├── v1/
│   │   │   ├── auth.py          # 注册、登录接口
│   │   │   ├── user.py          # 用户信息接口
│   │   │   ├── game_actions.py  # 游戏行为接口 (炼丹、突破等)
│   │   │   └── websocket.py     # WebSocket通信管理
│   ├── core/                    # 核心游戏逻辑
│   │   ├── game_loop.py         # 核心挂机循环 (每分钟/五分钟计算收益)
│   │   └── systems/             # 各游戏系统的逻辑实现
│   │       ├── cultivation_system.py # 修为、境界、突破逻辑
│   │       ├── combat_system.py      # 副本、战斗逻辑
│   │       ├── alchemy_system.py     # 炼丹逻辑
│   │       ├── farm_system.py        # 农场逻辑
│   │       └── luck_system.py        # 气运系统核心逻辑
│   ├── database/                # 数据库相关
│   │   ├── models.py            # SQLAlchemy数据模型 (User, Character, Item等)
│   │   ├── database.py          # 数据库连接和会话配置
│   │   └── crud.py              # 数据库增删改查操作封装
│   ├── config.py                # 配置文件 (数据库地址, 密钥等)
│   └── tests/                   # 测试代码
│
├── shared/                      # 客户端和服务端共享的代码
│   ├── schemas.py               # Pydantic数据模型 (DTOs), 规范通信数据结构
│   └── constants.py             # 游戏常量 (境界名称, 物品ID, 事件类型等)
│
├── .gitignore
├── requirements.txt             # 项目依赖库
├── README.md                    # 项目说明文档
├── start_server.bat             # 服务器启动脚本 (Windows)
└── start_client.bat             # 客户端启动脚本 (Windows)

## 🚀 快速启动

### 方式1: 使用启动脚本 (推荐)

**启动服务器:**
```bash
# Windows
start_server.bat

# 或手动执行
python server/main.py
```

**启动客户端:**
```bash
# Windows
start_client.bat

# 或手动执行
python client/main.py
```

### 🔧 故障排除

如果遇到PyQt6导入问题：
1. 重新安装PyQt6: `pip uninstall PyQt6 && pip install PyQt6`
2. 安装Visual C++运行库
3. 或尝试使用PyQt5: `pip install PyQt5`

## ✅ 当前完成状态

### 步骤1-3: 基础架构 ✅ 已完成
- [x] 共享模块开发
- [x] 服务端基础架构
- [x] 用户认证系统

### 步骤4: 客户端基础框架 ✅ 已完成
- [x] `client/network/api_client.py` - HTTP请求封装
- [x] `client/state_manager.py` - 客户端状态管理
- [x] `client/ui/login_window.py` - 登录注册界面
- [x] `client/main.py` - 客户端启动入口
- [x] 项目结构优化和文件清理
- [x] PyQt6兼容性问题解决

## 🎮 游戏核心设计

### 角色系统
- **一账号一角色**: 每个用户账号只有一个角色，注册后自动创建
- **随机灵根**: 角色创建时根据稀有度权重随机分配灵根类型
- **用户名即角色名**: 简化设计，使用用户名作为角色名

### API接口变更
- 移除角色创建接口 `/api/v1/user/characters` (POST)
- 新增角色获取接口 `/api/v1/user/character` (GET) - 自动创建如果不存在
- 新增角色详情接口 `/api/v1/user/character/detail` (GET) - 包含装备信息
- 简化背包装备接口，移除角色ID参数

玩法细节丰富与深化
让我们围绕“气运”这个核心，把你的想法变得更加丰满有趣。
核心属性与“气运”的联动
•	气运值 (Luck Value):
o	来源: 每日签到（抽签决定今日基础气运）、使用“转运丹”。

o	核心影响:
1.	修炼: 气运高时，挂机可能触发“顿悟”，获得额外大量修为；气运低时，可能“走火入魔”，修为不增反减。
2.	突破: 直接影响基础成功率。气运高，成功率大增；气运低，几乎必定失败。
3.	产出: 影响农场收货是否会变异（普通草药变灵药）、炼丹是否会出极品丹药、副本掉落的品质和数量。

模块功能
1.	背包 (Backpack) & 个人信息 (Profile)
o	个人信息: 除了现有属性，增加 灵根 (如金木水火土天灵根，影响修炼速度和功法契合度)、道号 (玩家自定义)、功法 (修炼的主要功法，影响修为获取效率和战斗技能)。
o	背包: 分为“仓库”、“装备”、“材料”、“丹药”、“种子”、“杂物”等多个标签，方便整理。

2.	洞府 (Cave Abode)
o	核心功能: 突破境界。
o	升级系统: 洞府本身可以升级，升级需要消耗灵石（金币的高级货币）和特殊材料。
o	子建筑:
	聚灵阵: 提升洞府的灵气浓度，直接增加挂机修为获取速度。
	丹房: 提升炼丹成功率，减少炸炉风险。

3.	商场 (Mall) & 交易 (Trading)
o	官方商场: 只出售基础物品，如低级种子、转运丹、新手装备。避免官方出售影响游戏平衡的强力道具。
o	玩家交易所 (Auction House): 这应该是经济系统的核心。玩家可以匿名或实名上架任何非绑定物品（装备、丹药、稀有材料），设定价格，其他玩家购买。服务器收取少量手续费（金币），作为金币回收的手段。
o	P2P交易: 增加一个安全的面对面交易窗口，防止欺诈。

4.	农场 (Spirit Farm)
o	土地: 土地有“品级”之分（贫瘠、普通、肥沃、灵田），高级土地需要开垦。
o	种子: 除了普通种子，副本和奇遇会产出稀有灵植种子。
o	环境影响: 农场的灵气浓度（受洞府聚灵阵影响）、天气（随机事件）、以及玩家的“气运”都可能导致作物变异，产生意想不到的收获。
o	互动: 可以帮好友的农场除草、除虫，获得少量奖励，增加社交性。

5.	炼丹炉 (Alchemy Cauldron)
o	丹方 (Recipe): 丹方需要通过副本、任务、商场购买或奇遇获得。
o	炼制过程: 引入“火候”小游戏。在炼丹时，需要玩家简单操作（如在特定时间点击），操作越好，成丹品质越高，出极品丹的概率也越大。当然，也可以选择“自动炼制”，成功率和品质由炼丹等级和丹房等级决定。
o	丹毒 (Pill Toxin): 丹药吃多了会积累丹毒，丹毒过高会影响修炼效率，甚至在突破时引发心魔。需要“清心丹”之类的丹药来清除。

6.	副本 (Instance)
o	类型:
	日常秘境: 消耗精力，产出经验、金币、基础材料。难度低。
	妖兽巢穴: 产出特定炼丹/炼器材料和装备。
	上古遗迹: 每周限次进入，难度高，需要特定道具或组队，产出高级功法、稀有装备和丹方。

7.	团战 (Team Battle)
o	魔君降临 (World Boss): 定时（如每周六晚8点）在特定地图刷新世界Boss。所有玩家都可以参与攻击，根据伤害排名发放奖励。最后一击的玩家/队伍有额外大奖。

8.	日志 (Log)
o	分类显示: 务必将日志分类！例如：“修炼日志”、“物品变动”、“财务记录”、“江湖恩怨”（谁攻击了你，你和谁交易了）。这样玩家可以清晰地回顾发生的一切。




