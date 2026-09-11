# 执行与配置

Python 3.10+，阶段运行器只用标准库。实际转模还需要用户自己的源文件，以及按项目配置的 Blender、Source 2 编译/检查工具。仓库不提供游戏工具或其它人物资产。

## 建立项目

```text
python skill/scripts/create_project.py --id my_character --source <用户模型目录或文件> --workspace projects/my_character
```

可加 `--checkpoint appearance --checkpoint physics --checkpoint hitboxes`，或 `--hand-manifest <替代手模资源清单>`。默认引用本技能唯一随附角色资产：共用第一人称素手。

生成 project.json：素材路径、项目命名空间、工具配置、外观选择、第一人称/物理/hitbox/持枪/优化需求都位于该项目中。人物名称与骨架映射不会写入通用脚本。

```text
python skill/scripts/workflow.py plan projects/my_character/project.json
python skill/scripts/workflow.py start projects/my_character/project.json --run projects/my_character/run_01
```

模板的阶段是 agent：由当前 Codex 继续制作、验证并提交产物。终端运行器停在 `needs_authoring` 是等待实际建模/适配，不是已经自动完成所有模型转换，也不是用户需要亲自完成该阶段。

## 自动、检查点与证据

- auto：每个阶段都有快照；Codex 连续推进，直到完成或遇到实际缺失信息。
- checkpoints：只在配置指定的阶段 await review；用户真正确认后才 accept，不能因等待超时自行确认。
- command：接入参数化脚本，以 argv 数组执行，不经过 shell。退出码、success_marker 与 outputs 文件合同全部通过才算完成。
- agent：完成实际制作、写入 result.json/资产/报告后，使用 record 提交证据。不得只写 passed 掩盖未实现工作。

```text
python skill/scripts/workflow.py record <run> <stage> --evidence <实际验证JSON>
python skill/scripts/workflow.py status <run>
python skill/scripts/workflow.py resume <run>
python skill/scripts/workflow.py accept <run> <stage> --note "实际用户检查结论"
```

证据格式至少为 `{"status":"passed","summary":"具体完成内容","checks":[实际检查结果]}`。record 不等于用户验收，配置的 review gate 仍会暂停。退出码 0 完成、2 等待制作/检查、1 失败。

每阶段输出自己的目录；把关键 DMX/VMDL/预览和报告加入 outputs 才会逐文件保存快照。wardrobe/expressions 清单从前阶段复制到新阶段后再改，不修改旧文件。配置或已完成输出被改后 resume 会拒绝，需新建候选；支持故障恢复，但不会自动推断复杂建模修改的依赖范围。

command 支持 `{python}`、`{skill}`、`{run}`、`{config}` 与 variables。花括号字面量按 Python format_map 写成 `{{`、`}}`。脚本必须使用传入路径，不写死某个用户的 Steam 目录。

## 实现范围

已实现的是项目创建、阶段执行、快照、恢复、证据记录和配置接口。各角色的 DCC 建模/导出、约束解算、编译校验、依赖打包由 authoring 或项目 adapter 完成；不能声称所有人物已零适配自动转换。

换装与表情嘴型均为 reserve/unimplemented，语音驱动嘴型默认关闭；有配置模板不代表游戏功能已完成。项目工具版本/输入哈希属于复现记录，不作为通用流程的固定模型版本。
