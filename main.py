from mastodon import Mastodon
import pandas as pd
from tqdm import tqdm
import configparser

# Чтение конфигурационного файла
config = configparser.ConfigParser()
config.read('config.ini')

# Инициализация клиента Mastodon
mastodon = Mastodon(
    access_token=config['Mastodon']['access_token'],
    client_id=config['Mastodon']['client_id'],
    client_secret=config['Mastodon']['client_secret'],
    api_base_url=config['Mastodon']['api_base_url']
)

# Записать заголовок файла
with open('data.csv', 'w') as f:
    f.write('user,follower,following\n')

def fetch_followers(user_id):
    """Получить подписчиков пользователя."""
    followers = mastodon.account_followers(user_id)
    return followers

def fetch_following(user_id):
    """Получить пользователей, на которых подписан пользователь."""
    following = mastodon.account_following(user_id)
    return following

# Создайте прогресс-бар вне функции
pbar = tqdm(total=50000)  # 100 - это просто пример, замените это на ваше реальное количество итераций

def process_user(user_id, user_acct, depth=1):
    """Обработать пользователя, получить его подписчиков и подписки, и рекурсивно обработать их (до max_depth)."""
    max_depth = int(config['Settings']['max_depth'])
    # Инициализировать пустой список для данных
    data = []
    # Получить подписчиков и подписки
    followers = fetch_followers(user_id)
    for follower in followers:
        follower_acct = follower.acct if '@' in follower.acct else f"{follower.acct}@{config['User']['home_server']}"
        data.append({'user': user_acct, 'follower': follower_acct, 'following': ''})
        if depth < max_depth:
            process_user(follower.id, follower_acct, depth=depth + 1)

    following = fetch_following(user_id)
    for followee in following:
        followee_acct = followee.acct if '@' in followee.acct else f"{followee.acct}@{config['User']['home_server']}"
        data.append({'user': user_acct, 'follower': '', 'following': followee_acct})
        if depth < max_depth:
            process_user(followee.id, followee_acct, depth=depth + 1)

    # Обновите прогресс-бар
    pbar.update(len(followers) + len(following))
    pbar.set_description(f"Processing user {user_acct}")

    # Преобразовать данные в DataFrame и записать в файл
    df = pd.DataFrame(data)
    df.to_csv('data.csv', mode='a', header=False, index=False)


def get_account(username):
    """Получить аккаунт по его имени."""
    accounts = mastodon.account_search(username)
    if accounts:
        return accounts[0]
    return None

# Запустить процесс с вашим пользователем
account = get_account(config['User']['initial_user'])
if account is not None:
    user_acct = account['acct'] if '@' in account['acct'] else f"{account['acct']}@{config['User']['home_server']}"
    process_user(account['id'], user_acct)
else:
    print("Пользователь не найден.")
