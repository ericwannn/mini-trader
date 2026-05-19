"""检查微信依赖"""
try:
    from wechat_driver import WeChat
    print("✅ wechat-driver 已安装")
except ImportError:
    print("❌ wechat-driver 未安装，需要安装")
