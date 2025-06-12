import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from app import db

from app.models import Chatroom, ChatroomMember, ChatroomMessage, FriendMessage, Friendships, User

fake = Faker('zh_CN')


class UniqueNicknameGenerator:
    def __init__(self):
        # 初始化所有词汇库
        self.phenomena = ['晨露', '晚风', '山雾', '溪声', '月光', '雪痕', 
                        '云影', '星辉', '雨滴', '晴光', '林雾', '霜迹']
        self.plants = ['与茉莉', '染青苔', '浸竹叶', '拂蔷薇', '润茶蘼',
                     '映白桦', '湿木樨', '暖松针', '绕藤蔓', '照蒲公英']
        self.times = ['阳光', '清晨', '黄昏', '星空', '海洋',
                             '森林']
        self.spaces = ['漫步', '时光',
                              '旋律', '画卷', '梦境']
        self.verbs = ['听溪', '数星', '拾露', '折光', '捕风', '藏雪',
                     '煮雨', '扫云', '酿月', '剪霞', '叠雾']
        self.elements = ['少年', '旅者',
                       '时节', '手札', '往事', '残稿']
        self.reduplication = ['簌簌', '疏疏', '泠泠', '潇潇', '皎皎', '沉沉',
                            '飒飒', '漠漠', '翦翦', '粼粼', '袅袅', '瑟瑟']
        self.scenes = ['落樱', '松涛', '竹露', '苇雪', '苔痕', '枫火',
                     '荻花', '梅影', '萤光', '云脚', '鹤踪']
        
        # 记录已使用的词汇组合
        self.used_combinations = set()
        
    def generate_unique_nickname(self):
        """生成确保用词不重复的网名"""
        max_attempts = 100  # 防止无限循环
        for _ in range(max_attempts):
            style = random.choice([1, 2, 3, 4])
            
            if style == 1 and self.phenomena and self.plants:
                # 自然现象+植物组合
                phenomena = random.choice(self.phenomena)
                plant = random.choice(self.plants)
                nickname = phenomena + plant
                
                # 检查组合是否唯一
                if nickname not in self.used_combinations:
                    self.used_combinations.add(nickname)
                    self.phenomena.remove(phenomena)
                    self.plants.remove(plant)
                    return nickname
                    
            elif style == 2 and self.times and self.spaces:
                # 时间+空间意境
                time = random.choice(self.times)
                space = random.choice(self.spaces)
                nickname = time + space
                
                if nickname not in self.used_combinations:
                    self.used_combinations.add(nickname)
                    self.times.remove(time)
                    self.spaces.remove(space)
                    return nickname
                    
            elif style == 3 and self.verbs and self.elements:
                # 感官动词+自然元素
                verb = random.choice(self.verbs)
                element = random.choice(self.elements)
                nickname = verb + element
                
                if nickname not in self.used_combinations:
                    self.used_combinations.add(nickname)
                    self.verbs.remove(verb)
                    self.elements.remove(element)
                    return nickname
                    
            elif style == 4 and self.reduplication and self.scenes:
                # 叠词+自然景物
                redup = random.choice(self.reduplication)
                scene = random.choice(self.scenes)
                nickname = redup + scene
                
                if nickname not in self.used_combinations:
                    self.used_combinations.add(nickname)
                    self.reduplication.remove(redup)
                    self.scenes.remove(scene)
                    return nickname
        
        # 如果尝试多次仍未生成，返回提示
        return "无法生成新的唯一昵称(词库可能已耗尽)"


def generate_users(count=20):
    """生成用户数据"""
    if User.query.first():
        return
    users = [
        User(
            name='mofei',
            nickname='莫非',
            password=generate_password_hash('123456'),
            avatar='/media/avatar/1746957099370.png',
        ),
        User(
            name='lujiao',
            nickname='鹿角',
            password=generate_password_hash('123456'),
            avatar='/media/avatar/1746962159203.jpeg',
        ),
    ]
    generator = UniqueNicknameGenerator()
    for i in range(count - 2):
        user = User(
            name=fake.user_name(),
            nickname=generator.generate_unique_nickname(),
            password=generate_password_hash('123456'),
            avatar=f'/media/avatar/avatar_{random.randint(1, 10)}.png',
        )
        users.append(user)

    try:
        db.session.add_all(users)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # 如果用户名冲突，重新生成
        return generate_users(db, count)

    # 随机选择头像
    avatars = [
        '1749712728781.jpeg',
        '1749712730259.jpg',
        '1749712731369.jpeg',
        '1749712732966.jpeg',
        '1749712734812.jpeg',
        '1749712735328.jpg',
        '1749712735726.jpeg',
        '1749712737102.jpg',
        '1749712740037.png',
        '1749712740629.jpeg',
        '1749712742603.jpeg',
        '1749712744530.jpeg',
        '1749712747017.jpg',
        '1749712749866.jpeg',
    ]
    for i in range(3, 21):
        user = db.session.scalars(
            select(User).where(User.id == i)
        ).first()
        user.avatar = f'/media/avatar/{random.choice(avatars)}'
    db.session.commit()


def generate_chatrooms():
    if Chatroom.query.first():
        return
    names = [
        '书虫俱乐部',
        '电竞狂潮',
        '美食研究所',
        '旅行漫游者',
        '健身狂热',
        '音乐星球',
        '追剧小分队',
        '投资与理财',
        '艺术与设计',
        '萌宠乐园',
        '极简生活家',
        '汽车发烧友',
        '时尚穿搭志',
        '神秘学与占星',
        '科技未来派',
    ]
    for name in names:
        is_private = random.choices([True, False], [1, 3])[0]
        creator_id = random.randint(1, 20)
        chatroom = Chatroom(
            name=name,
            is_private=is_private,
            creator_id=creator_id
        )
        db.session.add(chatroom)
    db.session.commit()


def generate_chatroom_members():
    if ChatroomMember.query.first():
        return
    # 将mofei用户加入所有私密聊天室
    user = db.session.scalars(
        select(User).where(User.name == 'mofei')
    ).first()
    chatrooms = db.session.scalars(
        select(Chatroom).where(Chatroom.is_private.is_(True))
    ).all()
    for chatroom in chatrooms:
        member = ChatroomMember(
            chatroom_id=chatroom.id,
            user_id=user.id
        )
        db.session.add(member)
    # 将所有用户加入书虫俱乐部
    users = db.session.scalars(
        select(User).where(User.name != 'mofei')
    ).all()
    chatroom = db.session.scalars(
        select(Chatroom).where(Chatroom.name == '书虫俱乐部')
    ).first()
    for user in users:
        member = ChatroomMember(
            chatroom_id=chatroom.id,
            user_id=user.id
        )
        db.session.add(member)
    db.session.commit()


def generate_chatroom_messages():
    if ChatroomMessage.query.first():
        return
    # 给书虫俱乐部添加50条消息
    messages = []
    chatroom_id = 1  # 书虫俱乐部的 chatroom_id
    start_time = datetime(2025, 6, 2, 12, 0, 0)
    current_time = start_time
    message_id = 1

    # 随机选择 2 条消息撤回
    recalled_indices = random.sample(range(50), 2)

    # 随机散聊30条
    while len(messages) < 30:
        content = random.choice([
            "有人看过《小王子》吗？适合成年人读吗？",
            "求推荐历史书！",
            "你们看书会做笔记吗？",
            "东野圭吾的新书怎么样？",
        ])
        messages.append({
            "id": message_id,
            "content": content,
            "sender_id": random.randint(1, 20),
            "chatroom_id": chatroom_id,
            "is_recalled": (message_id - 1 in recalled_indices),
            "recall_time": current_time + timedelta(minutes=1) if (message_id - 1 in recalled_indices) else None,
            "created_at": current_time,
        })
        message_id += 1
        current_time += timedelta(seconds=random.randint(30, 300))  # 间隔 30s~5min

    # 模拟对话主题
    topics = [
        {"starter": "电子书 vs 纸质书，你们更喜欢哪种？", "replies": [
            "纸质书！翻页的感觉无法替代",
            "电子书方便，出门带几百本",
            "我两种都买，经典书收藏纸质版",
        ]},
        {"starter": "有人一起读《百年孤独》吗？", "replies": [
            "我在读！但人物关系好乱😵",
            "建议做笔记，不然容易混淆",
            "读完震撼，魔幻现实主义巅峰",
        ]},
        {"starter": "大家最近在读什么书？求推荐！", "replies": [
            "我在看《三体》，科幻迷必读！",
            "刚读完《活着》，哭得不行😭",
            "推荐《人类简史》，视角很独特",
        ]},
    ]
    for topic in topics:
        current_time += timedelta(seconds=random.randint(240, 480))  

        # 初始提问（用户随机）
        sender_id = random.randint(1, 20)
        messages.append({
            "id": message_id,
            "content": topic["starter"],
            "sender_id": sender_id,
            "chatroom_id": chatroom_id,
            "is_recalled": (message_id - 1 in recalled_indices),
            "recall_time": current_time + timedelta(minutes=2) if (message_id - 1 in recalled_indices) else None,
            "created_at": current_time,
        })
        message_id += 1
        current_time += timedelta(seconds=random.randint(10, 120))  # 间隔 10s~2min

        # 生成回复
        for reply in topic["replies"]:
            reply_sender = random.randint(1, 20)
            messages.append({
                "id": message_id,
                "content": reply,
                "sender_id": reply_sender,
                "chatroom_id": chatroom_id,
                "is_recalled": (message_id - 1 in recalled_indices),
                "recall_time": current_time + timedelta(minutes=2) if (message_id - 1 in recalled_indices) else None,
                "created_at": current_time,
            })
            message_id += 1
            current_time += timedelta(seconds=random.randint(5, 60))  # 间隔 5s~1min
    
    for message in messages:
        db.session.add(ChatroomMessage(**message))
    db.session.commit()


def generate_friendships():
    if Friendships.query.first():
        return
    # 给mofei用户添加8个好友
    user = db.session.scalars(
        select(User).where(User.name == 'mofei')
    ).first()
    friends = []
    friends.append(
        db.session.scalars(
            select(User).where(User.name == 'lujiao')
        ).first()
    )
    users = db.session.scalars(
        select(User).where(User.id >= 3)
    ).all()
    for i in range(7):
        friend = random.choice(users)
        friends.append(friend)
        users.remove(friend)
    for friend in friends:
        friendship = Friendships(
            user_id=user.id,
            friend_id=friend.id
        )
        db.session.add(friendship)
        friendship = Friendships(
            user_id=friend.id,
            friend_id=user.id
        )
        db.session.add(friendship)
    db.session.commit()


def generate_friend_messages():
    contents = [
        '嗨，你最近在读什么书？',
        '刚看完《追风筝的人》，哭惨了😭 你呢？',
        '我也读过！卡勒德·胡赛尼的文笔太揪心了…',
        '对啊，尤其是哈桑那句“为你，千千万万遍” 🥺',
        '你平时喜欢纸质书还是电子书？',
        '纸质书！喜欢翻页的感觉，还能写批注~',
        '我也是！不过电子书出差方便，纠结…',
        '哈哈，我两种都买，经典书收藏纸质版！',
        '有道理！对了，推荐你读《解忧杂货店》，风格很温暖~',
        '东野圭吾的？好！我下一本就读它！',
    ]
    messages = []
    message_id = 12
    current_time = datetime(2025, 6, 2, 15, 0, 0)
    for i in range(0, len(contents), 2):
        messages.append({
            "id": message_id,
            "content": contents[i],
            "sender_id": 1,
            "receiver_id": 2,
            "is_recalled": False,
            "recall_time": None,
            "created_at": current_time,
        })
        message_id += 1
        current_time += timedelta(seconds=random.randint(15, 45))  # 间隔 15s~45s

        if i+1 == 7:
            # 插入一条撤回消息
            messages.append({
                "id": message_id,
                "content": contents[i+1],
                "sender_id": 2,
                "receiver_id": 1,
                "is_recalled": True,
                "recall_time": current_time + timedelta(seconds=23),
                "created_at": current_time,
            })
            message_id += 1
            current_time += timedelta(seconds=random.randint(5, 15))
        
        messages.append({
            "id": message_id,
            "content": contents[i+1],
            "sender_id": 2,
            "receiver_id": 1,
            "is_recalled": False,
            "recall_time": None,
            "created_at": current_time,
        })
        message_id += 1
        current_time += timedelta(seconds=random.randint(15, 45))  # 间隔 15s~45s
    
    for message in messages:
        db.session.add(FriendMessage(**message))
    db.session.commit()


def generate_mock_data():
    """生成所有模拟数据"""
    print('生成用户数据...')
    generate_users()

    print('生成聊天室数据...')
    generate_chatrooms()

    print('生成聊天室成员数据...')
    generate_chatroom_members()

    print('生成聊天室消息数据...')
    generate_chatroom_messages()

    print('生成好友数据...')
    generate_friendships()

    print('生成好友消息数据...')
    generate_friend_messages()


if __name__ == '__main__':
    from app import create_app, db

    app = create_app()
    with app.app_context():
        # db.drop_all()
        # db.create_all()
        generate_mock_data()
