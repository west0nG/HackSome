# V7 全新 Company E2E：启动前证据

- 日期：2026-07-14
- 新 Company ID：`v7-three-layer-e2e-20260714`
- Account：`foundagent`
- 启动前不存在该 Company state 目录，也不存在任何带 Company label 的容器。
- Docker Server：`29.5.3`
- CUA 镜像：`sha256:eb91cf6ae9ec466cfd13d4868361b2c63d490b260e223810ee023be41164d65b`
- 只确认 `accounts/foundagent/codex-auth.json` 与 `secrets.env` 存在；未读取或记录内容。

启动前既有 Company 文件聚合指纹：

| Company | SHA-1 聚合指纹 |
|---|---|
| `firsttest` | `6fb58c7d66128845b7c34195711abc8eadfb7ff6` |
| `foundagent` | `392e514ea7f9429d2edc2cf544a749e6fa80448a` |
| `fourthtest` | `fd1ea7adcbcc813afa7429f0755e2d75c72dc3cf` |
| `secondtest` | `92252c922e7b64626c5efce434f507468d87d2a1` |
| `thirdtest` | `0d2900f7e525a9502320a2f46fe9918d07e112b2` |

指纹算法：对目录内全部普通文件按路径排序，逐文件 `shasum` 后再对结果聚合 `shasum`。E2E 结束后使用同一算法复核。
