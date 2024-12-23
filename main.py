import requests
import networkx as nx
import matplotlib.pyplot as plt
import time

ACCESS_TOKEN = 'c79b0b65c79b0b65c79b0b659dc7e36f1ccc79bc79b0b65a743cc491d40249cc9a9b76a'
VERSION = '5.131'

usernames = ['serzh454545', 'feuk_228', 'negodno99']
FRIENDS_LIMIT = 100


def get_user_ids(usernames):
    url = f"https://api.vk.com/method/users.get?user_ids={','.join(usernames)}&access_token={ACCESS_TOKEN}&v={VERSION}"
    response = requests.get(url)
    data = response.json()

    if 'error' in data:
        print("Ошибка в запросе:", data['error']['error_msg'])
        return {}

    return {user['id']: user.get("screen_name", "") for user in data.get('response', [])}


def get_friends(user_id):
    url = f"https://api.vk.com/method/friends.get?user_id={user_id}&count={FRIENDS_LIMIT}&access_token={ACCESS_TOKEN}&v={VERSION}"
    response = requests.get(url)
    data = response.json()

    if 'error' in data:
        print(f"Ошибка при получении друзей для пользователя {user_id}: {data['error']['error_msg']}")
        return []

    return data.get('response', {}).get('items', [])


def calculate_eigenvector_centrality(G):
    try:
        return nx.eigenvector_centrality(G, max_iter=500)
    except nx.PowerIterationFailedConvergence:
        print("Сходимость не достигнута для всего графа. Рассчитываем для компонент связности.")
        centrality = {}
        for component in nx.connected_components(G):
            subgraph = G.subgraph(component)
            centrality.update(nx.eigenvector_centrality(subgraph, max_iter=500))
        return centrality


def main():
    user_ids = get_user_ids(usernames)
    if not user_ids:
        print("Не удалось получить ID пользователей. Проверьте запросы.")
        return

    friends_data = {}

    for user_id in user_ids:
        friends = get_friends(user_id)
        friends_data[user_id] = friends

        for friend_id in friends:
            friends_of_friend = get_friends(friend_id)
            friends_data[friend_id] = friends_of_friend
            time.sleep(0.3)

    G = nx.Graph()

    for user_id, friends in friends_data.items():
        for friend in friends:
            G.add_edge(user_id, friend)

    if len(G.edges()) == 0:
        print("Граф пустой, нет данных для оценки центральностей.")
        return

    eigenvector = calculate_eigenvector_centrality(G)
    closeness = nx.closeness_centrality(G)
    betweenness = nx.betweenness_centrality(G)

    group_members = {user_ids[user_id] for user_id in user_ids if user_ids[user_id] != ''}
    valid_labels = {user_id: user_ids[user_id] for user_id in group_members if user_ids.get(user_id)}

    # Используем kamada_kawai_layout для уменьшения наслоений
    pos = nx.kamada_kawai_layout(G)

    plt.figure(figsize=(200, 200))

    # Настройки размеров и цветов узлов
    node_sizes = [800 * closeness.get(node, 0.1) for node in G.nodes()]
    node_colors = [eigenvector.get(node, 0.1) for node in G.nodes()]

    # Рисуем граф
    nx.draw(G, pos, with_labels=False, node_color=node_colors, node_size=node_sizes,
            cmap=plt.cm.RdYlBu, edge_color="gray", alpha=0.7)

    # Подписываем только корректные узлы (никнеймы)
    nx.draw_networkx_labels(G, pos, labels=valid_labels, font_size=20, font_weight='bold', font_color='black')

    # Подписываем ID пользователей над точками
    id_labels = {node: str(node) for node in G.nodes()}  # Создаем словарь для отображения ID
    nx.draw_networkx_labels(G, pos, labels=id_labels, font_size=12, font_color='blue')  # Отображаем ID с меньшим шрифтом

    plt.savefig("graph_output.png")
    print("График сохранён в файл graph_output.png")

    group_eigenvector = {user_ids[user_id]: eigenvector.get(user_id, 0) for user_id in user_ids}
    group_closeness = {user_ids[user_id]: closeness.get(user_id, 0) for user_id in user_ids}
    group_betweenness = {user_ids[user_id]: betweenness.get(user_id, 0) for user_id in user_ids}

    print("Eigenvector Centrality for Group Members:")
    for member, centrality in group_eigenvector.items():
        if centrality > 0:
            print(f"{member}: {centrality}")

    print("\nCloseness Centrality for Group Members:")
    for member, centrality in group_closeness.items():
        if centrality > 0:
            print(f"{member}: {centrality}")

    print("\nBetweenness Centrality for Group Members:")
    for member, centrality in group_betweenness.items():
        if centrality > 0:
            print(f"{member}: {centrality}")


if __name__ == "__main__":
    main()
