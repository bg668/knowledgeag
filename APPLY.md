# REQ-KM-001 patch overlay

把本压缩包内容覆盖到仓库根目录，然后执行：

```bash
pytest -q tests/test_source_versioning.py
pytest -q
```

本次修改实现：

- 同一 `uri + content_hash` 重复导入复用已有 source/version。
- 同一 URI 内容变化后生成新 version，并保持相同 source_id。
- `sources` 表改为 `(source_id, version_id)` 复合主键，并保留 `UNIQUE(uri, version_id)`。
- evidence 回源时按 `(source_id, source_version)` 获取精确 SourceVersion，避免取到最新版本。
