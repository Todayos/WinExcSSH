# WinExcSSH

## 配置
修改配置文件 config.config.yml 中的内容，主要包含以下内容

### HostInfo 
> 服务器IP与端口

### UserInfo
> SSH的名用户名与密码

### PceKeys
> 定位进程的关键字，该关键字应该只会查询到同一类服务进程

### TfiifPath
> 启动或停止服务脚本所在的文件路径

### StartCommand
> 启动服务所使用的启动命令

### StopCommand
> 停止服务所使用的停止命令

## 执行
> 执行 python start.py 命令可启动服务
> 
> 执行上述命令前，请确认该包已被添加进python包查找路径

## 设置windows快捷方式
修改TFIIF.bat脚本
如: cmd /k python C:\Projects\start-tfiif-package\WinExcSSH\start.py，将C:\Projects\start-tfiif-package\WinExcSSH\start.py启动文件路径更换为当前环境中start.py文件所在的路径，在文件系统中打开该文件，发送快捷方式到桌面即可完成快捷方式的创建,后续双击桌面快捷方式即可启动服务器中的相关服务。
>
> 快捷方式可重新命名，如将上述发送的快捷方式名称"TFIIF.bat - 快捷方式"重命名为"TFIIF"