"""阶段 6 消融条件定义（SPEC §10.4）：A 逐条去规则 1–11；B 禁 move_first/compress/delete；F 去意图分类。"""


def ablation_A():
    return [{"name": "A_full", "remove": None}] + \
           [{"name": f"A_no{k}", "remove": k} for k in range(1, 12)]


def ablation_B():
    return [
        {"name": "B_full", "disable": []},
        {"name": "B_no_move_first", "disable": ["move_first"]},
        {"name": "B_no_compress", "disable": ["compress"]},
        {"name": "B_no_delete", "disable": ["delete"]},
    ]


def ablation_F():
    return [{"name": "F_full", "intent": True}, {"name": "F_no_intent", "intent": False}]
