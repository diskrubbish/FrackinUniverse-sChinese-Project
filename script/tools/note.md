## 启动器

### Startranz.py

还没写完的GUI，也不想写了。

### translation_console.py

临时写的简陋GUI，帮助使用者更便捷的操作.

## 非依赖库部分

### extract_labels_config.py

核心配置参数。


### parser_settings.py

过滤Path的规则列表。用正则过滤。由于体量较大，所以没有并入extract_labels_config.py。



## 依赖库部分


### json_tools.py

为stb不规范json进行规范化的函数所用依赖库。

### patch_tool.py

处理patch的函数所用依赖库，非常不好用。

### stbtran_utils.py

核心依赖库，很冗杂。

### requests_tool、para_api.py

为操作paratranz所写的依赖。

### special_cases.py、shared_path.py

老格式的过滤器之一，过滤电子人前缀和相同文本。

对于paratranz格式已经过时，等待被移除。

### export_mod_para.py

导出可以供stb使用patch的依赖，等待优化。

### translation_memory.py

为操作翻译所写的依赖。等待优化。
