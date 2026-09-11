# CS2 Character Workflow

通用 CS2 角色转模工作流：**用户提供人物素材，工作流复用一套第一人称基础手模**。

不绑定特定人物、固定骨骼数量或历史模型版本。衣服、头发、耳朵、尾巴、妆容、瞳色、物理、受击框和持枪参数都在用户项目中配置。每角色袖套单独制作；基础手部网格、UV 和蒙皮可复用。

## 包含什么

- Codex 技能与完整阶段制作说明：素材/外观 → 骨骼 → 第一人称手袖和腿 → 物理 → hitbox → 单模型持枪 → 优化 → 编译 → 验证 → 交付。
- Python 项目创建和阶段运行器：自动推进、指定检查点、逐阶段快照、失败恢复、产物哈希、实际制作证据。
- 唯一随附角色资产：[第一人称素手](skill/assets/shared-hands/manifest.json)，含源网格与必要材质依赖。
- [物理响应调校](skill/references/physics.md)：分开处理大束头发的柔软度、回正速度、低速响应与射击驱动，保存独立候选和编译差异；具体链和参数由用户模型决定。
- 换装、表情、嘴型与眨眼的配置及体积预算接口，**尚未实现游戏控制**，后续可逐项完善。

人物模型、服装、脸/眼贴图、耳尾、历史试验模型、游戏工具与运行输出不在仓库内。

## 在 Codex 使用

将 `skill` 目录安装为 Codex 技能目录中的 `cs2-character-workflow`，也可直接让 Codex 读取仓库内 `skill/SKILL.md`：

> 使用 $cs2-character-workflow 处理我提供的人物，复用基础手模，自动保存阶段快照；造型、物理和受击框完成时让我检查。

技能由 Codex 执行建模与适配。运行器管理流程，**不是任意 FBX 零适配的全自动转换器**。换装/表情状态保持未完成，不因建立项目就变成可用功能。

## 命令行入口

Python 3.10+。实际转模工具通过项目配置提供。

```powershell
python skill/scripts/create_project.py --id my_character --source "D:/MyCharacter" --workspace projects/my_character --checkpoint appearance --checkpoint physics
python skill/scripts/workflow.py plan projects/my_character/project.json
python skill/scripts/workflow.py start projects/my_character/project.json --run projects/my_character/run_01
```

`needs_authoring` 表示由 Codex 继续该阶段的实际制作。完成并验证后提交证据，配置的用户检查点仍会暂停；详细命令见 [执行器说明](skill/references/runner.md)。

## 后续扩展与优化

[换装](skill/references/wardrobe.md)：一个角色骨架/模型中管理衣服、耳尾的网格组和妆容/瞳色材质选择，并联动身体遮挡、第一人称袖套和物理。计算整套选项总包、单套显示成本和每个新选项增量；隐藏网格仍占文件体积。

[表情与嘴型](skill/references/expressions.md)：保留用户源模型的 Morph/形态键、面部骨骼或嘴部网格组。共享基础脸，优化时同步所有变形目标并检查张嘴、眨眼与叠加；不为每个衣服/妆容/表情组合复制完整资源。

两项目前均仅预留接口。语音嘴型驱动也未实现。

## 验证

```powershell
python -m unittest discover -s tests -v
```

测试覆盖流程行为与共用手资源完整性，不把它们当作所有角色的游戏效果/伤害验证。各用户项目的候选包、自己/Bot 测试指令、实际结果和回退点由该项目交付。
