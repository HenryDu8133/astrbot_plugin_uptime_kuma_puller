from datetime import datetime
import aiohttp
from astrbot.api.event import filter
from astrbot.api.star import Star, register, Context
from astrbot.api.message_components import Plain
from astrbot.api import AstrBotConfig
from astrbot.api import logger

@register("UptimeKuma状态监控", "Henry_Du", "UptimeKuma状态查询插件", "1.8", "https://github.com/HenryDu8133/astrbot_plugin_uptime_kuma_puller")
class UptimeKumaPuller(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.query_url = config.get("query_url")
        self.proj_name_list = config.get("proj_name_list")
        
        if not self.query_url or not self.proj_name_list:
            logger.warning("请先在管理面板配置 query_url 和 proj_name_list")
            self.is_configured = False
        else:
            self.is_configured = True

    @filter.command("健康", alias={"uptime", "状态查询"})
    async def handle_uptime_query(self, ctx):
        if not self.is_configured:
            logger.warning("插件未配置，无法处理请求")
            return await ctx.send(ctx.make_result().message("❌插件未配置，请先在管理面板配置 query_url 和 proj_name_list"))
        
        logger.info(f"收到状态查询请求：{ctx.message_str}")

        if not ctx.message_str:
            return await ctx.send(ctx.make_result().message("❌请输入 '。健康 <项目>' (唤醒符可替换)查看服务器组状态"))

        message = ctx.message_str.strip()

        proj_name = message[len("健康"):].strip() if message.startswith("健康") else message[len("uptime"):].strip()
        
        if not proj_name:
            return await ctx.send(ctx.make_result().message("❌请输入 '。健康 <项目>' (唤醒符可替换)查看服务器组状态"))
        
        proj_name = proj_name.lower()
        if proj_name not in self.proj_name_list:
            return await ctx.send(ctx.make_result().message(f"❌{proj_name} 不在列表（{str(self.proj_name_list)}）中，请重新输入！"))
        
        try:
            result = await self.OrangeUptimeQuery(proj_name)
            return await ctx.send(ctx.make_result().message(result))
        except Exception as e:
            logger.error(f"查询状态时发生错误：{str(e)}")
            return await ctx.send(ctx.make_result().message("❌查询状态时发生错误，请稍后再试"))

    def takeSecond(self, elem):
        return elem[1]

    async def get_uptime_kuma_status(self, proj_name: str) -> dict:
        """获取Uptime Kuma状态"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)  
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.query_url}/api/status-page/{proj_name}") as response:
                    if response.status != 200:
                        logger.error(f"API请求失败，状态码：{response.status}")
                        raise Exception(f"API请求失败，状态码：{response.status}")
                    return await response.json()
        except asyncio.TimeoutError:
            logger.error("获取Uptime Kuma状态超时")
            return {}
        except Exception as e:
            logger.error(f"获取Uptime Kuma状态失败：{str(e)}")
            return {}

    async def get_heartbeat_status(self, proj_name: str) -> dict:
        """获取心跳状态"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)  
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.query_url}/api/status-page/heartbeat/{proj_name}") as response:
                    if response.status != 200:
                        logger.error(f"心跳API请求失败，状态码：{response.status}")
                        raise Exception(f"心跳API请求失败，状态码：{response.status}")
                    return await response.json()
        except asyncio.TimeoutError:
            logger.error("获取心跳状态超时")
            return {}
        except Exception as e:
            logger.error(f"获取心跳状态失败：{str(e)}")
            return {}

    async def OrangeUptimeQuery(self, proj_name):
        content_js = await self.get_uptime_kuma_status(proj_name)
        if not content_js:
            return "❌无法获取Uptime Kuma状态，请检查配置和网络连接"

        heartbeat_content_js = await self.get_heartbeat_status(proj_name)
        if not heartbeat_content_js:
            return "❌无法获取心跳状态，请检查配置和网络连接"

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
                    if pub_sbj["tags"] != []:
                        tag = f"[{pub_sbj['tags'][0]['name']}]"
                pub_sbj_name = f"{tag}{pub_sbj['name']}"
                pub_list_ids.append([pub_sbj["id"], pub_sbj_name])

        # 查询每个监控项的情况
        heartbeat_list = heartbeat_content_js.get("heartbeatList", {})
        for i in range(len(pub_list_ids)):
            pub_sbj = pub_list_ids[i]
            if str(pub_sbj[0]) not in heartbeat_list or not heartbeat_list[str(pub_sbj[0])]:
                continue
            heartbeat_sbj = heartbeat_list[str(pub_sbj[0])][-1]
            if heartbeat_sbj["status"] == 1:
                status = "🟢[在线]"
            else:
                status = "🔴[离线]"
            ping = f" {heartbeat_sbj['ping']}ms" if heartbeat_sbj["ping"] is not None else ""
            temp_txt = f"{status}{ping}"
            pub_list_ids[i].append(temp_txt)

 
        temp_txt = ""
        maintenance_list = content_js.get("maintenanceList", [])
        for maintenance in maintenance_list:
            try:
                title = maintenance.get("title", "无标题")
                content = maintenance.get("description", "无描述")
                start_time = maintenance.get("startDate")
                end_time = maintenance.get("endDate")
                time_info = ""
                if start_time and end_time:
                    start_time = datetime.fromtimestamp(start_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    end_time = datetime.fromtimestamp(end_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    time_info = f"\n\n⏲️维护时间：{start_time} - {end_time}"
                
                temp_txt += f"""\n🔵【维护中】{title}\n{content}{time_info}\n\n==============\n"""
            except Exception as e:
                logger.error(f"处理维护消息时出错：{str(e)}")
                logger.debug(f"维护消息原始数据：{maintenance}")

        # 处理事件公告
        incident_list = content_js.get("incidentList", [])
        if not incident_list:
            logger.info("未找到事件公告列表，尝试从旧字段获取")
            incident = content_js.get("incident", None)
            if incident:
                incident_list = [incident]
        style_map = {
            "info": "信息",
            "warning": "警告",
            "danger": "危险",
            "primary": "主要",
            "light": "明亮",
            "dark": "黑暗"
        }

        for incident in incident_list:
            try:
                style = style_map.get(incident.get("style", "info").lower(), "信息")
                title = incident.get("title", "无标题")
                content = incident.get("content", "无内容")
                u_time = incident.get("lastUpdatedDate")
                time_info = ""
                if u_time:
                    try:
                        dt = datetime.strptime(u_time, '%Y-%m-%d %H:%M:%S')
                        time_info = f"\n⏲️本通知更新于{dt.strftime('%Y-%m-%d %H:%M:%S')}"
                    except (ValueError, TypeError):
                        time_info = f"\n⏲️本通知更新于{u_time}"
                
                temp_txt += f"""\n📣【{style}】{title}\n{content}{time_info}\n"""
            except Exception as e:
                logger.error(f"处理事件公告时出错：{str(e)}")
                logger.debug(f"事件公告原始数据：{incident}")

        if temp_txt:
            temp_txt = "\n==============\n" + temp_txt

        logger.debug(f"维护消息数量：{len(maintenance_list)}")
        logger.debug(f"事件公告数量：{len(incident_list)}")
        logger.debug(f"最终公告内容：{temp_txt}")

        pub_list_ids.sort(key=self.takeSecond)
        for pub_sbj in pub_list_ids:
            ret += f"{pub_sbj[1]} {pub_sbj[2]}\n"
        ret += temp_txt

        up_count = 0
        down_count = 0
        for pub_sbj in pub_list_ids:
            if len(pub_sbj) > 2:
                if "🟢" in pub_sbj[2]:
                    up_count += 1
                elif "🔴" in pub_sbj[2]:
                    down_count += 1

        msg += f"🟢{proj_title}\n✅ 正常：{up_count}  ❌ 异常：{down_count}\n{ret}\n*******"
        return msg