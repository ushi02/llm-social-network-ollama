from constants_and_utils import *
from generate_personas import *
import argparse
import json
import numpy as np
import pandas as pd
import time

def get_persona_format(demos_to_include, lang='en'):
    """
    Define persona format for GPT: eg, "ID. Name - Gender, Age, Race/ethnicity, Religion, Political Affiliation".
    """
    if lang == 'zh':
        persona_format = '编号. '
        if 'name' in demos_to_include:
            persona_format += '姓名 - '
        for demo in demos_to_include:
            if demo != 'name':
                persona_format += f'{ZH_FIELD_NAMES[demo]}，'
        return persona_format[:-1]  # remove trailing '，'

    if lang == 'ja':
        persona_format = 'ID. '
        if 'name' in demos_to_include:
            persona_format += '名前 - '
        for demo in demos_to_include:
            if demo != 'name':
                persona_format += f'{JA_FIELD_NAMES[demo]}、'
        return persona_format[:-1]  # remove trailing '、'

    persona_format = 'ID. '
    if 'name' in demos_to_include:
        persona_format += 'Name - '
    for demo in demos_to_include:
        if demo != 'name':
            persona_format += f'{demo.capitalize()}, '
    persona_format = persona_format[:-2]  # remove trailing ', '
    return persona_format


def get_system_prompt(method, personas, demos_to_include, curr_pid=None, G=None,
                      only_degree=True, num_choices=None, include_reason=False, all_demos=False, lang='en'):
    """
    Get content for system message.
    """
    assert method in {'global', 'local', 'sequential', 'iterative-add', 'iterative-drop'}
    if G is not None:
        assert 'iterative' in method
    if (curr_pid is not None) or include_reason:
        assert method != 'global'
    if num_choices is not None:
        assert method in {'local', 'sequential'}
        assert num_choices >= 1

    if lang == 'zh':
        return get_system_prompt_zh(method, personas, demos_to_include, curr_pid=curr_pid, G=G,
                                     only_degree=only_degree, num_choices=num_choices,
                                     include_reason=include_reason, all_demos=all_demos)
    if lang == 'ja':
        return get_system_prompt_ja(method, personas, demos_to_include, curr_pid=curr_pid, G=G,
                                     only_degree=only_degree, num_choices=num_choices,
                                     include_reason=include_reason, all_demos=all_demos)

    # commonly used strings
    persona_format = get_persona_format(demos_to_include)
    persona_format = f'where each person is described as \"{persona_format}\"'
    prompt_extra = 'Do not include any other text in your response. Do not include any people who are not listed below.'
    if all_demos:
        prompt_extra = 'Pay attention to all demographics. ' + prompt_extra
    if curr_pid is not None:
        prompt_personal = assign_persona_to_model(personas[curr_pid], demos_to_include) + '.'

    if method == 'global':
        prompt = 'Your task is to create a realistic social network. You will be provided a list of people in the network, ' + persona_format + '. Provide a list of friendship pairs in the format ID, ID with each pair separated by a newline. ' + prompt_extra
    
    elif method in {'local', 'sequential'}:
        prompt = prompt_personal + ' You are joining a social network.\n\nYou will be provided a list of people in the network, ' + persona_format
        if method == 'sequential':
            prompt += ', followed by '
            if only_degree:
                prompt += 'their current number of friends'
            else:
                prompt += 'their current friends\' IDs'
        prompt += '.\n\nWhich of these people will you become friends with? '
        if num_choices is not None:
            pp = 'people' if num_choices > 1 else 'person'
            prompt += f'Choose {num_choices} {pp}. '
        if include_reason:
            prompt += 'Provide a list of *YOUR* friends and a short reason for why you are befriending them, in the format:\nID, reason\nID, reason\n...\n\n'
            prompt += 'IMPORTANT: Respond with ONLY the ID,reason pairs. Do not include any introductory text, explanations, or closing remarks. '
            prompt += 'Your entire response should consist solely of lines in the format "ID, reason". Start immediately with the first ID.\n\n'
        else:
            prompt += 'Provide a list of *YOUR* friends in the format ID, ID, ID, etc. ' 
            prompt += 'CRITICAL: Respond with ONLY numbers and commas. '  
            prompt += 'Do not include explanations, names, periods, or any other text. '  
            prompt += 'Your entire response must be a single line like: 28,11,22,32 '
        prompt += prompt_extra
    
    elif method == 'iterative-add':
        prompt = prompt_personal + ' You are part of a social network and you want to make a new friend.\n\nYou will be provided a list of potential new friends, ' + persona_format + ', followed by their total number of friends and number of mutual friends with you. '
        curr_friends = ', '.join(list(G.neighbors(curr_pid)))
        prompt += 'Keep in mind that you are already friends with IDs ' + curr_friends + '.\n\nWhich person in this list are you likeliest to befriend? '
        if include_reason:
            prompt += 'Provide your answer in JSON form: {\"new friend\": ID, \"reason\": reason for adding friend}. '
        else:
            prompt += 'Answer by providing ONLY this person\'s ID. '
        prompt += prompt_extra
    
    else:  # iterative-drop
        prompt = prompt_personal + ' Unfortunately, you are busy with work and unable to keep up all your friendships.\n\nYou will be provided a list of your current friends, ' + persona_format + ', followed by their total number of friends and number of mutual friends with you.'
        prompt += '\n\nWhich friend in this list are you likeliest to drop? '
        if include_reason:
            prompt += 'Provide your answer in JSON form: {\"dropped friend\": ID, \"reason\": reason for dropping friend}. '
        else:
            prompt += 'Answer by providing ONLY this friend\'s ID. '
        prompt += prompt_extra
    return prompt


def get_system_prompt_zh(method, personas, demos_to_include, curr_pid=None, G=None,
                          only_degree=True, num_choices=None, include_reason=False, all_demos=False):
    """
    Chinese version of get_system_prompt (--lang zh).
    """
    persona_format = get_persona_format(demos_to_include, lang='zh')
    persona_format = f'每个人的描述格式为"{persona_format}"'
    prompt_extra = '回复中不要包含任何其他文字。不要包含下面列表中没有出现的人。'
    if all_demos:
        prompt_extra = '请注意所有人口统计学信息。' + prompt_extra
    if curr_pid is not None:
        prompt_personal = assign_persona_to_model(personas[curr_pid], demos_to_include, lang='zh') + '。'

    if method == 'global':
        prompt = '你的任务是创建一个真实的社交网络。下面会给你网络中所有人的列表，' + persona_format + '。请以 编号,编号 的格式列出好友关系对，每对占一行。' + prompt_extra

    elif method in {'local', 'sequential'}:
        prompt = prompt_personal + '你正在加入一个社交网络。\n\n下面会给你网络中其他人的列表，' + persona_format
        if method == 'sequential':
            prompt += '，以及'
            if only_degree:
                prompt += '他们当前的好友数量'
            else:
                prompt += '他们当前好友的编号'
        prompt += '。\n\n你会和这些人中的哪些人成为朋友？'
        if num_choices is not None:
            prompt += f'请选择 {num_choices} 个人。'
        if include_reason:
            prompt += '请列出*你自己*的好友以及交友的简短理由，格式如下：\n编号, 理由\n编号, 理由\n...\n\n'
            prompt += '重要：只能回复"编号, 理由"这样的行，不要包含任何引言、解释或结束语。'
            prompt += '你的整个回复必须只包含这种格式的行，从第一个编号直接开始。\n\n'
        else:
            prompt += '请以 编号,编号,编号 的格式列出*你自己*的好友列表。'
            prompt += '关键要求：只能包含数字和逗号。'
            prompt += '不要包含解释、姓名、句号或任何其他文字。'
            prompt += '你的完整回复必须是单独一行，例如：28,11,22,32 '
        prompt += prompt_extra

    elif method == 'iterative-add':
        prompt = prompt_personal + '你是这个社交网络的一员，想要交一个新朋友。\n\n下面会给你一份潜在新朋友的列表，' + persona_format + '，以及他们的好友总数和与你的共同好友数量。'
        curr_friends = '，'.join(list(G.neighbors(curr_pid)))
        prompt += '请记住你已经和编号 ' + curr_friends + ' 的人是朋友。\n\n这份列表里你最可能和哪个人交朋友？'
        if include_reason:
            prompt += '请以 JSON 格式回答：{"new friend": 编号, "reason": 交朋友的理由}。'
        else:
            prompt += '只需回答这个人的编号。'
        prompt += prompt_extra

    else:  # iterative-drop
        prompt = prompt_personal + '很不幸，你最近工作繁忙，无法维系所有的友谊。\n\n下面会给你一份你现有好友的列表，' + persona_format + '，以及他们的好友总数和与你的共同好友数量。'
        prompt += '\n\n这份列表里你最可能和哪个朋友断绝往来？'
        if include_reason:
            prompt += '请以 JSON 格式回答：{"dropped friend": 编号, "reason": 断绝往来的理由}。'
        else:
            prompt += '只需回答这个朋友的编号。'
        prompt += prompt_extra
    return prompt


def get_system_prompt_ja(method, personas, demos_to_include, curr_pid=None, G=None,
                          only_degree=True, num_choices=None, include_reason=False, all_demos=False):
    """
    Japanese version of get_system_prompt (--lang ja).
    """
    persona_format = get_persona_format(demos_to_include, lang='ja')
    persona_format = f'各人は"{persona_format}"の形式で説明されます'
    prompt_extra = '回答には他の文章を含めないでください。以下に記載されていない人物を含めないでください。'
    if all_demos:
        prompt_extra = 'すべての人口統計情報に注意してください。' + prompt_extra
    if curr_pid is not None:
        prompt_personal = assign_persona_to_model(personas[curr_pid], demos_to_include, lang='ja') + '。'

    if method == 'global':
        prompt = 'あなたの仕事は現実的なソーシャルネットワークを作ることです。ネットワーク内の全員のリストが渡されます。' + persona_format + '。友人関係のペアを ID,ID の形式で、1行ずつ改行して列挙してください。' + prompt_extra

    elif method in {'local', 'sequential'}:
        prompt = prompt_personal + 'あなたはソーシャルネットワークに参加しようとしています。\n\nネットワーク内の他の人々のリストが渡されます。' + persona_format
        if method == 'sequential':
            prompt += '、さらに'
            if only_degree:
                prompt += '現在の友達の人数'
            else:
                prompt += '現在の友達のID'
        prompt += '。\n\nこの中の誰と友達になりますか？'
        if num_choices is not None:
            prompt += f'{num_choices}人選んでください。'
        if include_reason:
            prompt += '*あなたの*友達のリストと、それぞれ友達になる簡単な理由を次の形式で答えてください：\nID, 理由\nID, 理由\n...\n\n'
            prompt += '重要：「ID, 理由」の形式の行のみで回答してください。前置き、説明、締めの言葉は含めないでください。'
            prompt += '回答全体をこの形式の行だけにし、最初のIDから直接始めてください。\n\n'
        else:
            prompt += '*あなたの*友達のリストを ID,ID,ID の形式で提供してください。'
            prompt += '重要：数字とカンマのみで回答してください。'
            prompt += '説明、名前、ピリオド、その他の文章は含めないでください。'
            prompt += '回答は次のような1行のみにしてください：28,11,22,32 '
        prompt += prompt_extra

    elif method == 'iterative-add':
        prompt = prompt_personal + 'あなたはソーシャルネットワークの一員で、新しい友達を作りたいと思っています。\n\n新しい友達候補のリストが渡されます。' + persona_format + '、さらに彼らの友達の総数とあなたとの共通の友達の数。'
        curr_friends = '、'.join(list(G.neighbors(curr_pid)))
        prompt += 'あなたはすでにID ' + curr_friends + ' の人たちと友達であることに注意してください。\n\nこのリストの中で、あなたが最も友達になりそうなのは誰ですか？'
        if include_reason:
            prompt += 'JSON形式で答えてください：{"new friend": ID, "reason": 友達になる理由}。'
        else:
            prompt += 'この人のIDのみを答えてください。'
        prompt += prompt_extra

    else:  # iterative-drop
        prompt = prompt_personal + '残念ながら、あなたは仕事が忙しく、すべての友人関係を維持できません。\n\n現在の友達のリストが渡されます。' + persona_format + '、さらに彼らの友達の総数とあなたとの共通の友達の数。'
        prompt += '\n\nこのリストの中で、あなたが最も絶交しそうなのは誰ですか？'
        if include_reason:
            prompt += 'JSON形式で答えてください：{"dropped friend": ID, "reason": 絶交する理由}。'
        else:
            prompt += 'この友達のIDのみを答えてください。'
        prompt += prompt_extra
    return prompt


def get_user_prompt(method, personas, order, demos_to_include, curr_pid=None,
                    G=None, only_degree=True, lang='en'):
    """
    Get content for user message.
    """
    assert method in {'global', 'local', 'sequential', 'iterative-add', 'iterative-drop'}
    lines = []
    if method == 'global':
        for pid in order:
            lines.append(convert_persona_to_string(personas[pid], demos_to_include, pid=pid, lang=lang))

    elif method == 'local':
        assert curr_pid is not None
        for pid in order:
            if pid != curr_pid:
                lines.append(convert_persona_to_string(personas[pid], demos_to_include, pid=pid, lang=lang))
        assert len(lines) == (len(order)-1)

    elif method == 'sequential':
        assert curr_pid is not None
        assert G is not None
        for pid in order:
            if pid != curr_pid:
                persona = convert_persona_to_string(personas[pid], demos_to_include, pid=pid, lang=lang)
                cand_friends = set(G.neighbors(pid))  # candidate's friends
                if lang == 'zh':
                    if only_degree:
                        persona += f'；好友数：{len(cand_friends)}'
                    elif len(cand_friends) == 0:
                        persona += '；暂无好友'
                    else:
                        persona += '；好友编号：' + '，'.join(cand_friends)
                elif lang == 'ja':
                    if only_degree:
                        persona += f'。友達の数：{len(cand_friends)}'
                    elif len(cand_friends) == 0:
                        persona += '。まだ友達がいません'
                    else:
                        persona += '。友達のID：' + '、'.join(cand_friends)
                else:
                    if only_degree:
                        persona += f'; has {len(cand_friends)} friends'
                    elif len(cand_friends) == 0:
                        persona += '; no friends yet'
                    else:
                        persona += '; friends with IDs ' + ', '.join(cand_friends)
                lines.append(persona)
        assert len(lines) == (len(order)-1)

    else:  # iterative
        assert curr_pid is not None
        assert G is not None
        friends = list(G.neighbors(curr_pid))
        if method == 'iterative-add':
            id_list = list(set(G.nodes()) - set(friends) - {curr_pid})  # non-friends
            action = {'zh': '交朋友', 'ja': '友達になる'}.get(lang, 'befriend')
        else:
            id_list = friends  # current friends
            action = {'zh': '断绝往来', 'ja': '絶交する'}.get(lang, 'drop')
        random.shuffle(id_list)
        for pid in id_list:
            persona = convert_persona_to_string(personas[pid], demos_to_include, pid=pid, lang=lang)
            cand_friends = set(G.neighbors(pid))  # candidate's friends
            mutuals = set(friends).intersection(cand_friends)
            if lang == 'zh':
                lines.append(persona + f'；好友数：{len(cand_friends)}，共同好友数：{len(mutuals)}')
            elif lang == 'ja':
                lines.append(persona + f'。友達の数：{len(cand_friends)}、共通の友達の数：{len(mutuals)}')
            else:
                lines.append(persona + f'; # friends: {len(cand_friends)}, # mutual friends: {len(mutuals)}')
        if lang == 'zh':
            id_list_str = '，'.join(id_list)
            lines.append(f'编号 {id_list_str} 中，你最可能和谁{action}？')
        elif lang == 'ja':
            id_list_str = '、'.join(id_list)
            lines.append(f'ID {id_list_str} の中で、あなたが最も{action}しそうなのは誰ですか？')
        else:
            id_list_str = ', '.join(id_list)
            lines.append(f'Which person ID out of {id_list_str} are you likeliest to {action}?')

    prompt = '\n'.join(lines)
    return prompt
    

def update_graph_from_response(method, response, G, curr_pid=None, include_reason=False, num_choices=None):
    """
    Parse response from LLM and update graph based on edges found.
    Expectation:
    - 'global' response should list all edges in the graph
    - 'local' and 'sequential' should list all new edges for curr_pid
    - 'iterative-add' should list one new edge to add for curr_pid
    - 'iterative-drop' should list one existing edge to drop for curr_pid
    """
    assert method in {'global', 'local', 'sequential', 'iterative-add', 'iterative-drop'}
    if num_choices is not None:
        assert method in {'local', 'sequential'}
    if include_reason:
        assert method != 'global' and curr_pid is not None
        reasons = {}
    edges_found = []
    
    lines = response.split('\n')
    if method == 'global':
        for line in lines:
            id1, id2 = line.split(',')
            edges_found.append((id1.strip(), id2.strip()))
    
    elif method == 'local' or method == 'sequential':
        assert curr_pid is not None, f'{method} method needs curr_pid to parse response'
        new_edges = []
        if include_reason:
            for line in lines:
                if ',' in line:
                    pid, reason = line.strip('.').split(',', 1)
                    new_edges.append((curr_pid, pid.strip()))
                    reasons[pid] = reason.strip()
        else:
            assert len(lines) == 1, f'Response should not be more than one line'
            line = lines[0].replace(',', ' ').replace('.', ' ').replace('，', ' ').replace('。', ' ').replace('、', ' ')
            ids = line.split()
            for pid in ids:
                assert pid.isnumeric(), f'Response should contain ONLY the ID(s)'
                new_edges.append((curr_pid, pid.strip()))
        if num_choices is not None:
            pp = 'people' if num_choices > 1 else 'person'
            assert len(new_edges) == num_choices, f'Choose {num_choices} {pp}'
        edges_found.extend(new_edges)
    
    else:  # iterative-add or iterative-drop
        assert curr_pid is not None, f'{method} method needs curr_pid to parse response'
        if include_reason:
            resp = json.loads(response.strip())
            key = 'new friend' if method == 'iterative-add' else 'dropped friend'
            assert key in resp, f'Missing "{key}" in response'
            pid = str(resp[key])
            action = method.split('-')[1]
            reasons[(pid, action)] = reason
        else:
            assert len(lines) == 1, f'Response should not be more than one line'
            pid = lines[0].strip('.')
            assert len(pid.split()) == 1 and pid.isnumeric(), f'Response should contain only the ID of the person you\'re choosing'
        assert pid.lower() != 'none', 'You must choose one of the IDs in the list'
        edges_found.append((curr_pid, pid))
    
    orig_len = len(edges_found)
    edges_found = set(edges_found)
    if len(edges_found) < orig_len:
        print(f'Warning: {orig_len} edges were returned, {len(edges_found)} are unique')
    
    # check all valid
    valid_nodes = set(G.nodes())
    curr_edges = set(G.edges())
    for id1, id2 in edges_found:
        assert id1 in valid_nodes, f'{id1} is not a node in the network'
        assert id2 in valid_nodes, f'{id2} is not a node in the network'
        if method == 'iterative-drop':
            assert ((id1, id2) in curr_edges) or ((id2, id1) in curr_edges), f'{id2} is not an existing friend'

    # only modify graph at the end
    if method == 'iterative-drop':
        G.remove_edges_from(edges_found)
    else:
        G.add_edges_from(edges_found)
    if include_reason:
        return G, reasons 
    return G
    
    
def generate_network(method, demos_to_include, personas, order, model, mean_choices=None, include_reason=False,
                     all_demos=False, only_degree=True, num_iter=3, temp=None, verbose=False, lang='en'):
    """
    Generate entire network.
    """
    assert method in {'global', 'local', 'sequential', 'iterative'}
    G = nx.Graph()
    G.add_nodes_from(order)
    reasons = {}
    total_num_tries = 0
    total_input_toks = 0
    total_output_toks = 0

    if method == 'global':
        system_prompt = get_system_prompt(method, personas, demos_to_include, all_demos=all_demos, lang=lang)
        user_prompt = get_user_prompt(method, personas, order, demos_to_include, lang=lang)
        parse_args = {'method': method, 'G': G}
        G, response, num_tries = repeat_prompt_until_parsed(model, system_prompt, user_prompt, update_graph_from_response,
                                                            parse_args, temp=temp, verbose=verbose)
        total_num_tries += num_tries
        total_input_toks += len(system_prompt.split()) + len(user_prompt.split())
        total_output_toks += len(response.split())

    elif method == 'local' or method == 'sequential':
        order2 = np.random.choice(order, size=len(order), replace=False)  # order of adding nodes
        print('Order of assigning:', order2[:10])
        for node_num, pid in enumerate(order2):
            if mean_choices is None:
                num_choices = None
            else:
                num_choices = int(min(max(np.random.exponential(mean_choices), 1), 20))
            if node_num < 3:  # for first three nodes, use local
                system_prompt = get_system_prompt('local', personas, demos_to_include, curr_pid=pid,
                                    num_choices=num_choices, include_reason=include_reason, all_demos=all_demos, lang=lang)
                user_prompt = get_user_prompt('local', personas, order, demos_to_include, curr_pid=pid, lang=lang)
            else:  # otherwise, allow local or sequential
                system_prompt = get_system_prompt(method, personas, demos_to_include, curr_pid=pid,
                    num_choices=num_choices, include_reason=include_reason, all_demos=all_demos, only_degree=only_degree, lang=lang)
                user_prompt = get_user_prompt(method, personas, order, demos_to_include, curr_pid=pid,
                                               G=G, only_degree=only_degree, lang=lang)
            parse_args = {'method': method, 'G': G, 'curr_pid': pid, 'num_choices': num_choices, 'include_reason': include_reason}
            G, response, num_tries = repeat_prompt_until_parsed(model, system_prompt, user_prompt,
                    update_graph_from_response, parse_args, temp=temp, verbose=verbose)
            if include_reason:
                G, pid_reasons = G
                print(pid, pid_reasons)
                reasons[pid] = pid_reasons
            total_num_tries += num_tries
            total_input_toks += len(system_prompt.split()) + len(user_prompt.split())
            total_output_toks += len(response.split())

    else:  # iterative
        # construct local network first
        order2 = np.random.choice(order, size=len(order), replace=False)  # order of adding nodes
        for pid in order2:
            if mean_choices is None:
                num_choices = None
            else:
                num_choices = int(max(np.random.exponential(mean_choices), 1))
            system_prompt = get_system_prompt('local', personas, demos_to_include, curr_pid=pid,
                                num_choices=num_choices, include_reason=include_reason, all_demos=all_demos, lang=lang)
            user_prompt = get_user_prompt('local', personas, order, demos_to_include, curr_pid=pid, lang=lang)
            parse_args = {'method': 'local', 'G': G, 'curr_pid': pid, 'num_choices': num_choices, 'include_reason': include_reason}
            G, response, num_tries = repeat_prompt_until_parsed(model, system_prompt, user_prompt, 
                    update_graph_from_response, parse_args, temp=temp, verbose=verbose)
            if include_reason:
                G, pid_reasons = G 
                reasons[pid] = pid_reasons
            total_num_tries += num_tries
            total_input_toks += len(system_prompt.split()) + len(user_prompt.split())
            total_output_toks += len(response.split())
        print('Constructed initial network using local method')
        
        for it in range(num_iter):
            print(f'========= ITERATION {it} =========')
            order3 = np.random.choice(order2, size=len(order2), replace=False)  # order of rewiring nodes
            for pid in order3:  # iterate through nodes and rewire
                system_prompt = get_system_prompt('iterative-add', personas, demos_to_include,
                        curr_pid=pid, G=G, include_reason=include_reason, all_demos=all_demos, lang=lang)
                user_prompt = get_user_prompt('iterative-add', personas, None, demos_to_include,
                                              curr_pid=pid, G=G, lang=lang)
                parse_args = {'method': 'iterative-add', 'G': G, 'curr_pid': pid, 'include_reason': include_reason}
                G, response_add, num_tries = repeat_prompt_until_parsed(model, system_prompt, user_prompt, 
                        update_graph_from_response, parse_args, temp=temp, verbose=verbose)
                if include_reason:
                    G, pid_reasons = G 
                    reasons[pid] = pid_reasons
                total_num_tries += num_tries
                total_input_toks += len(system_prompt.split()) + len(user_prompt.split())
                total_output_toks += len(response_add.split())
                
                friends = list(G.neighbors(pid))
                if len(friends) > 1:
                    system_prompt = get_system_prompt('iterative-drop', personas, demos_to_include,
                            curr_pid=pid, G=G, include_reason=include_reason, all_demos=all_demos, lang=lang)
                    user_prompt = get_user_prompt('iterative-drop', personas, None, demos_to_include,
                                                  curr_pid=pid, G=G, lang=lang)
                    parse_args = {'method': 'iterative-drop', 'G': G, 'curr_pid': pid, 'include_reason': include_reason}
                    G, response_drop, num_tries = repeat_prompt_until_parsed(model, system_prompt, user_prompt, 
                            update_graph_from_response, parse_args, temp=temp, verbose=verbose)
                    if include_reason:
                        G, pid_reasons = G 
                        reasons[pid] = pid_reasons
                    total_num_tries += num_tries
                    total_input_toks += len(system_prompt.split()) + len(user_prompt.split())
                    total_output_toks += len(response_drop.split())
                else:  
                    assert len(friends) == 1  # must be at least 1 because we just added
                    G.remove_edge(pid, friends[0])
                print(pid, response_add, response_drop)
                
    return G, reasons, total_num_tries, total_input_toks, total_output_toks
   

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('method', type=str, choices=['global', 'local', 'sequential', 'iterative'])
    parser.add_argument('--persona_fn', type=str, default='us_50_gpt4o_w_interests.json')
    parser.add_argument('--mean_choices', type=int, default=-1)
    parser.add_argument('--include_names', action='store_true')
    parser.add_argument('--include_interests', action='store_true')
    parser.add_argument('--only_interests', action='store_true')
    parser.add_argument('--shuffle_all', action='store_true')
    parser.add_argument('--shuffle_interests', action='store_true')
    parser.add_argument('--include_friend_list', action='store_true')
    parser.add_argument('--include_reason', action='store_true')
    parser.add_argument('--prompt_all', action='store_true')
    parser.add_argument('--lang', type=str, default='en', choices=['en', 'zh', 'ja'])

    parser.add_argument('--model', type=str, default='gpt-3.5-turbo')
    parser.add_argument('--num_networks', type=int, default=1)
    parser.add_argument('--start_seed', type=int, default=0)  # set start seed to continue with new seeds
    parser.add_argument('--temp', type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument('--num_iter', type=int, default=3)  # only used when method is iterative
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    return args

def get_save_prefix_and_demos(args):
    """
    Get save prefix and demos to include based on args.
    """
    save_prefix = f'{args.method}_{args.model}'
    demos_to_include = []
    if args.mean_choices != -1:
        assert args.mean_choices > 0
        save_prefix += '_n' + str(args.mean_choices)
    if args.only_interests:
        save_prefix += '_only_interests'
        demos_to_include.append('interests')
    else:
        if args.include_names:
            save_prefix += '_w_names'
            demos_to_include.append('name')        
        demos_to_include.extend(['gender', 'age', 'race/ethnicity', 'religion', 'political affiliation'])
        if args.include_interests:
            save_prefix += '_w_interests'
            demos_to_include.append('interests')
    if args.shuffle_interests:
        assert args.include_interests or args.only_interests
        assert '_INTERESTS_SHUFFLED' in args.persona_fn
        save_prefix += '_INTERESTS_SHUFFLED'
    if args.shuffle_all:
        assert '_ALL_SHUFFLED' in args.persona_fn
        save_prefix += '_ALL_SHUFFLED'
    if args.include_friend_list:
        save_prefix += '_w_list'  # list of friends
    if args.include_reason:
        save_prefix += '_w_reason'
    if args.prompt_all:
        save_prefix += '_prompt_all'
    if args.temp != DEFAULT_TEMPERATURE:
        temp_str = str(args.temp).replace('.', '')
        save_prefix += f'_temp{temp_str}'
    if args.lang != 'en':
        save_prefix += f'_{args.lang}'
    return save_prefix, demos_to_include


if __name__ == '__main__':
    args = parse_args()
    save_prefix, demos_to_include = get_save_prefix_and_demos(args)
    print('save prefix:', save_prefix)
    fn = os.path.join(PATH_TO_TEXT_FILES, args.persona_fn)
    with open(fn) as f:
        personas = json.load(f)
    pids = list(personas.keys())
    print(f'Loaded {len(pids)} personas from {args.persona_fn}')

    stats = []    
    end_seed = args.start_seed+args.num_networks
    for seed in range(args.start_seed, end_seed):
        ts = time.time()
        np.random.seed(seed)
        order = np.random.choice(pids, size=len(pids), replace=False)  # order of printing personas
        print('Order of printing:', order[:10])
        G, reasons, num_tries, input_toks, output_toks = generate_network(
            args.method, demos_to_include, personas, order, args.model, 
            mean_choices=args.mean_choices if args.mean_choices > 0 else None,
            include_reason=args.include_reason, all_demos=args.prompt_all,
            only_degree=not args.include_friend_list, temp=args.temp, num_iter=args.num_iter, verbose=args.verbose,
            lang=args.lang)
        
        save_network(G, f'{save_prefix}_{seed}')
        draw_and_save_network_plot(G, f'{save_prefix}_{seed}')
        duration = time.time()-ts
        print(f'Seed {seed}: {len(G.edges())} edges, num tries={num_tries}, input toks={input_toks}, output toks={output_toks} [time={duration:.2f}s]')
        stats.append({'seed': seed, 'duration': duration, 'num_tries': num_tries, 
                      'num_input_toks': input_toks, 'num_output_toks': output_toks})
        if args.include_reason:
            fn = os.path.join(PATH_TO_TEXT_FILES, f'{save_prefix}_{seed}_reasons.json')
            with open(fn, 'w') as f:
                json.dump(reasons, f)
    
    stats_df = pd.DataFrame(stats, columns=['seed', 'duration', 'num_tries', 'num_input_toks', 'num_output_toks'])
    save_dir = os.path.join(PATH_TO_STATS_FILES, save_prefix)
    if not os.path.exists(save_dir):
        print('Making directory:', save_dir)
        os.makedirs(save_dir)
    stats_fn = os.path.join(PATH_TO_STATS_FILES, save_prefix, f'cost_stats_s{args.start_seed}-{end_seed-1}.csv')
    stats_df.to_csv(stats_fn, index=False)
