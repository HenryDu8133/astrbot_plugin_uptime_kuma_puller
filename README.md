# astrbot_plugin_uptime_kuma_puller
UptimeKuma状态监控查询插件<br>
[![AstrBot Uptime Kuma Puller](https://img.shields.io/badge/AstrBot_Uptime_Kuma_Puller-6ce197?style=for-the-badge&logo=github&logoColor=white)](https://github.com/HenryDu8133/astrbot_plugin_uptime_kuma_puller)<br>
[![GitHub Release](https://img.shields.io/badge/Plugin_v1.0-8a4cff?style=flat-square&logo=github)](https://github.com/HenryDu8133/astrbot_plugin_uptime_kuma_puller)
[![GitHub Stars](https://img.shields.io/github/stars/HenryDu8133/astrbot_plugin_uptime_kuma_puller?style=flat-square&logo=github&label=Stars&color=blue)](https://github.com/HenryDu8133/astrbot_plugin_uptime_kuma_puller)
[![GitHub Downloads](https://img.shields.io/github/downloads/HenryDu8133/astrbot_plugin_uptime_kuma_puller/latest/total?style=flat-square&label=Download%20Latest&color=green)](https://github.com/HenryDu8133/astrbot_plugin_uptime_kuma_puller/releases/latest)

## 📖说明
- 本插件基于bananaxiao2333的https://github.com/bananaxiao2333/nonebot-plugin-uptime-kuma-puller <br>
  经过修改后适用于AstrBOT

---
## 💿安装
 - 可通过AstrBOT的插件市场安装
 - 或下载**整个仓库**

---
## ⚙️使用方法
**1** 请在`main.py`文件中**第10行**填写你的UptimeKuma地址[![Uptime Kuma](https://img.shields.io/badge/Uptime_Kuma-6ce197?style=flat&logo=github&logoColor=white)](https://github.com/louislam/uptime-kuma) <br>
```python
self.query_url = "http://your.ip" # 填写你的UptimeKuma地址
```
**2** 请在`main.py`文件中**第11行**填写你的监控面板项目名称（图中绿框的内容）
![image](https://github.com/user-attachments/assets/7a4a2592-28c0-4dc7-94d0-2aef3f8e0347)
> 如果有多个，可以`["示例1","示例2"]`

**3** 全部设置完后，重载插件即可
