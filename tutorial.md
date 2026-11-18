# Muse 用量小组件 · 安装 + 数据搭建

利用你自己的 Muse 一段话在 GitHub 搭好数据连接的用量小组件，桌面上一眼看清本周额度、永久额度和重置时间。整个过程分两半：**组件**点下面的链接一键安装；**数据**让你的 Muse 在 GitHub 上建一个仓库，每 30 分钟把你的 Muse 用量写进去，给你一个**专属数据链接**，填进组件就是你自己的用量了。

## 准备

- 一个已登录的 **Muse**
- iPhone 上装 **Scripting** App（App Store 免费）
- 一个 GitHub 账号（没有的话，让 Muse 指导你注册并连接）

## 第一步：安装组件

点这个链接，在 Scripting 里确认导入即可：

[一键安装「Muse 用量」组件](https://scripting.fun/import_scripts?urls=%5B%22https%3A%2F%2Fraw.githubusercontent.com%2FLu6618%2Fmuse-usage-widget%2Fmain%2Fmuse-2.scripting%22%5D)

装好先不用管，组件里没有任何人的数据，等第二步拿到你自己的数据链接再填。

## 第二步：把这段话发给你的 Muse

整段复制发送：

> 帮我建一条 Muse 用量数据管线，做完把数据链接给我：
>
> 1. 在我的 GitHub 上新建一个**公开**仓库 `muse-usage-widget`，在里面建 `data/muse_usage.json`，格式如下（数值先填占位）：
>
> ```json
> {
>   "updated_at": "2026-11-18T14:00:00+08:00",
>   "plan": "Free",
>   "percent_used": 0,
>   "resets_at": "2026-11-23T14:12:00+08:00",
>   "additional_tokens": { "percent_used": 0, "left_label": "3B tokens left" }
> }
> ```
>
> 字段含义：`plan` 是套餐名；`percent_used` 是本周额度**已用**百分比；`resets_at` 是本周额度重置时间；`additional_tokens` 是永久（额外）额度的已用百分比和剩余量文本；`updated_at` 是这份数据的更新时间。
>
> 2. 给我建一个**每 30 分钟**运行的定时任务：查询我的 Muse 订阅用量，按上面的格式更新 `data/muse_usage.json` 并推送到这个仓库。成功时静默，失败时告诉我。
>
> 3. 做完后，把数据直链发给我，格式是 `https://raw.githubusercontent.com/<我的GitHub用户名>/muse-usage-widget/main/data/muse_usage.json`，并带我验收一遍。

## 第三步：验收并填入组件

1. 打开 Muse 给你的数据直链，能看到一段 JSON。
2. 看 `updated_at`：应该是最近 30 分钟内的时间。
3. 看 `percent_used`：应该是你真实的用量百分比（不是占位的 0 了）。
4. 三项都对，在 Scripting 里运行「muse 用量」，在打开的设置页里粘贴你的数据链接保存；再把组件加到桌面（长按桌面 →「+」→ Scripting → 选「muse 用量」）。

## 出问题时

- **直链打不开 / 404** → 仓库没设成公开，让 Muse 改成 Public。
- **`updated_at` 一直不变** → 定时任务停了，让 Muse 检查那条每 30 分钟的任务。
- **数字不是你的** → 把你打开直链看到的内容发给 Muse，让它核对写的是不是你的订阅用量。

---

*说明：仓库里的 JSON 只有用量百分比和时间，不含任何账号信息，所以可以放心设为公开。*
