---
title: AI Infra
date: '2026-11-04'
tags:
- 系统工程
- 模型推理
- 性能分析
---

# AI Infra

本栏以推理与数据基础设施为当前主线，再逐步扩展到训练、通信与算子优化。[完整学习路线](../2026-11-04-ai-infra-agent-roadmap.md)。

## 先建立三个能力

- **测量**：区分模型计算、输入处理、排队、通信和 I/O；固定负载并保留基线。
- **解释**：用内存、缓存、并发、设备执行与通信的证据解释现象。
- **改进**：一次验证少量变化，同时观察吞吐、延迟、资源占用和失败率。

## 建议逐步记录的主题

| 主题 | 核心问题 | 建议实验 |
| --- | --- | --- |
| PyTorch 与设备执行 | 时间花在算子、拷贝还是输入准备？ | 固定模型与输入，做一次 Profiler 分析 |
| 推理服务 | 并发、批处理和缓存如何影响服务表现？ | 固定输入输出长度，画出负载与延迟/吞吐的关系 |
| 数据与存储 | 读取、解码、分片或写回是否成为瓶颈？ | 对比各阶段耗时与峰值内存 |
| 训练与通信 | 显存和通信限制了哪些并行策略？ | 在可用多卡环境上比较 DDP 与 FSDP2 |
| 运行与部署 | 如何定位超时、OOM、重试和服务退化？ | 保存日志、配置、健康检查与恢复步骤 |

## 官方入口

- [PyTorch Profiler](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html)
- [vLLM 基准工具](https://docs.vllm.ai/en/stable/benchmarking/cli/)
- [PyTorch DDP](https://docs.pytorch.org/tutorials/intermediate/ddp_tutorial.html)
- [PyTorch FSDP2](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html)

## 可按需查阅的历史资料

- [内存与缓存](../System/04-memory.md)
- [进程、线程与同步](../OS/操作系统2-进程&线程.md)
- [SMORE 大规模系统阅读笔记](../Papers-old/论文阅读笔记25：SMORE大规模知识图谱系统.md)
- [异构分布式机器学习阅读笔记](../Papers-old/论文阅读笔记30：异构分布式机器学习Partial Reduce.md)

后两篇作为系统设计案例保留，阅读重点是采样、资源管理和分布式执行。具体实现应结合当前框架文档验证。
