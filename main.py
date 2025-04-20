#from astrbot import Context, Config
from datetime import datetime
import aiohttp
from astrbot.api.event import filter
from astrbot.api.star import Star, register, Context
from astrbot.api.message_components import Plain
from astrbot.api import AstrBotConfig
from astrbot.api import logger  # 导入logger

@register("UptimeKuma状态监控", "", "UptimeKuma状态查询插件", "1.0", "")
class UptimeKumaPuller(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 使用配置并检查是否配置
        self.query_url = config.get("query_url")
        self.proj_name_list = config.get("proj_name_list")
        
        if not self.query_url or not self.proj_name_list:
            logger.warning("请先在管理面板配置 query_url 和 proj_name_list")  # 使用导入的logger
            self.is_configured = False
        else:
            self.is_configured = True

    @filter.command("健康", alias={"uptime", "状态查询"})
    async def handle_uptime_query(self, ctx):
        if not self.is_configured:
            return await ctx.send(ctx.make_result().message("❌插件未配置，请先在管理面板配置 query_url 和 proj_name_list"))
        # 获取消息文本
        message = ctx.message_str.strip()
        # 提取项目名称
        proj_name = message[len("健康"):].strip() if message.startswith("健康") else message[len("uptime"):].strip()
        
        if not proj_name:
            return await ctx.send(ctx.make_result().message("❌请输入 '健康 adl' (唤醒符可替换)查看ADL服务器组状态"))
        
        proj_name = proj_name.lower()
        if proj_name not in self.proj_name_list:
            return await ctx.send(ctx.make_result().message(f"❌{proj_name} 不在列表（{str(self.proj_name_list)}）中，请重新输入！"))
        
        result = await self.OrangeUptimeQuery(proj_name)
        await ctx.send(ctx.make_result().message(result))

    def takeSecond(self, elem):
        return elem[1]

    async def OrangeUptimeQuery(self, proj_name):
        main_api = f"{self.query_url}/api/status-page/{proj_name}"
        heartbeat_api = f"{self.query_url}/api/status-page/heartbeat/{proj_name}"
        ret = ""
        msg = ""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(main_api) as response:
                if response.status != 200:
                    msg += f"❌主要接口查询失败：Http error {response.status}"
                    return msg
                content_js = await response.json()

            async with session.get(heartbeat_api) as response:
                if response.status != 200:
                    msg += f"❌心跳接口查询失败：Http error {response.status}"
                    return msg
                heartbeat_content_js = await response.json()

        proj_title = content_js["config"]["title"]

        # 获取监控项名称列表
        pub_list = content_js["publicGroupList"]
        pub_list_ids = []
        for pub_group in pub_list:
            for pub_sbj in pub_group["monitorList"]:
                tag = ""
                if "tags" in pub_sbj:
                    print(pub_sbj)
                    if pub_sbj["tags"] != []:
                        tag = f"[{pub_sbj['tags'][0]['name']}]"
                pub_sbj_name = f"{tag}{pub_sbj['name']}"
                pub_list_ids.append([pub_sbj["id"], pub_sbj_name])

        # 查询每个监控项的情况
        heartbeat_list = heartbeat_content_js["heartbeatList"]
        for i in range(len(pub_list_ids)):
            pub_sbj = pub_list_ids[i]
            heartbeat_sbj = heartbeat_list[str(pub_sbj[0])][-1]
            if heartbeat_sbj["status"] == 1:
                status = "🟢[UP]"
            else:
                status = "🔴[DOWN]"
            ping = f" {heartbeat_sbj['ping']}ms" if heartbeat_sbj["ping"] is not None else ""
            temp_txt = f"{status}{ping}"
            pub_list_ids[i].append(temp_txt)

        # 获取公告
        temp_txt = ""
        incident = content_js["incident"]
        if incident is not None:
            style = str(incident["style"]).upper()
            title = str(incident["title"])
            content = str(incident["content"])
            u_time = str(incident["lastUpdatedDate"])
            temp_txt = f"""————\n📣【{style}】{title}\n{content}\n⏲️本通知更新于{u_time}\n————"""

        pub_list_ids.sort(key=self.takeSecond)
        for pub_sbj in pub_list_ids:
            ret += f"{pub_sbj[1]} {pub_sbj[2]}\n"
        ret += temp_txt

        msg += f"🟢{proj_title}\n{ret}\n*******"
        return msg