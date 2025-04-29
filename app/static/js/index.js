$(function () {
    // 初始化ueditor
    var ue = UE.getEditor('editor', {
        //这里可以选择自己需要的工具按钮名称,此处仅选择如下七个
        toolbars: [
            ['simpleupload', /*'insertimage',*/ 'emotion', 'scrawl']
        ],
        elementPathEnabled: false,
        initialFrameHeight: 98,
        maximumWords: 100,
        wordOverFlowMsg: '<span style="color:red;">你输入的字符个数已经超出最大允许值！</span>',
        autoHeightEnabled: false
    });
    // 在ueditor编辑中输入回车进行发送
    var domUtils = UE.dom.domUtils;
    ue.addListener('ready', function () {
        ue.focus(true);
        domUtils.on(ue.body, "keydown", function (event) {
            // 回车发送
            if (event.code == 'Enter') {
                event.preventDefault();
                // event.stopPropagation()
                console.log('发送')
                text = ue.getContent()
                if (ROOM) {
                    chatroom_id = $('.chatpnl').attr('data')
                    $.post('/api/v1/chatrooms/' + chatroom_id + '/chats', { content: text }, function (res) {
                        $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
                        ue.setContent('')
                    }, 'json')
                } else if (FRIEND) {
                    friend_id = $('.chatpnl').attr('data')
                    $.post('/api/v1/friends/' + friend_id + '/chats', { content: text }, function (res) {
                        $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
                        ue.setContent('')
                    }, 'json')
                }
            }
        })
    });

    // 请求失败时的处理
    $(document).ajaxError(function (event, jqXHR, ajaxOptions, thrownError) {
        // 统一错误处理
        const errorResponse = jqXHR.responseJSON;
        if (errorResponse) {
            alert(errorResponse.message);
            return
        }
    });

    // 点击聊天室按钮显示聊天室列表
    $('#chatroom_btn').click(function () {
        $('#friend_list').hide()
        $('#room_list').show()
        $.getJSON('/api/v1/chatrooms', function (rooms) {
            $('#room_list').empty()
            for (var i = 0; i < rooms.length; i++) {
                room = rooms[i]
                li = '<li data="' + room.id + '">\n' +
                    '                <div class="qun">\n' +
                    '                    <img src="/static/image/user.png" alt="聊天室" class="qunicon">\n' +
                    '                    <span>' + room.name + '</span>\n' +
                    '                    <span class="time">12:08</span>\n' +
                    '                </div>\n' +
                    '            </li>'
                $('#room_list').append(li)
            }

        })
    })
    // 点击+按钮显示创建聊天室窗口
    $('#add_chatroom_btn').click(function () {
        $('#add_chatroom_modal').modal()
    })
    // 创建聊天室窗口的创建按钮事件
    $('#add_chatroom_confirm_btn').click(function () {
        name = $('#chatroom_name').val().trim()
        $.post({
            url: '/api/v1/chatrooms',
            contentType: 'application/json',
            data: JSON.stringify({ name: name })
        }).done(function (res) {
            console.log('create chatroom: ', res);
            location.reload()
        });
    })
    // 点击聊天室列表的li进入对应的聊天室
    $('#room_list').on('click', 'li', function () {
        chatroom_name = $(this).find('span').eq(0).text()
        chatroom_id = $(this).closest('li').attr('data')
        $.getJSON('/api/v1/chatrooms/' + chatroom_id + '/chats', function (chats) {
            // 如果已经在聊天室，先发出离开聊天室信号
            if (ROOM) {
                socket.emit('leave_chatroom', { name: user_name, room: ROOM });
            }
            // 在页面上存储该聊天室信息
            $('.chatpnl').attr('data', chatroom_id)
            $('.chathead').text(chatroom_name)
            // 获取当前用户信息
            current_user_id = $('.user').attr('data')
            user_name = $('.user span').text()
            // 清空当前聊天区域
            $('.chat-content').empty()
            // 遍历获取的聊天记录，往聊天区域填充
            for (var i = 0; i < chats.length; i++) {
                chat = chats[i]
                div = '<div class="chat' + (chat.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
                    '                <div class="chat">\n' +
                    '                    <div class="chatinfo ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
                    '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
                    '                        <div>' + chat.sender_name + '</div>\n' +
                    '                    </div>\n' +
                    '                    <div class="chatcontent ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">' + chat.content + '</div>\n' +
                    '                    <div class="clear"></div>\n' +
                    '                </div>\n' +
                    '            </div>'
                $('.chat-content').append(div)
            }
            // 滑到最底部，查看最新的聊天内容
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            setTimeout(function () {
                $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            }, 100);
            // 发出进入聊天室信号
            socket.emit('join_chatroom', { name: user_name, room: chatroom_id });
            // 设置全局变量
            ROOM = chatroom_id
            FRIEND = null
            // 显示editor
            $('#editor').show()
        })
    })

    // 点击联系人按钮显示好友列表
    $('#friend_btn').click(function () {
        $('#room_list').hide()
        $('#friend_list').show()
        $.getJSON('/api/v1/friends', function (friends) {
            $('#friend_list').empty()
            for (var i = 0; i < friends.length; i++) {
                friend = friends[i]
                li = '<li data="' + friend.id + '">\n' +
                    '                <div class="qun">\n' +
                    '                    <img src="/static/image/user.png" alt="用户头像" class="qunicon">\n' +
                    '                    <span>' + friend.name + '</span>\n' +
                    '                    <span class="time">12:08</span>\n' +
                    '                </div>\n' +
                    '            </li>'
                $('#friend_list').append(li)
            }
        })
    })
    // 点击+按钮显示添加好友窗口
    $('#add_friend_btn').click(function () {
        $('#add_friend_modal').modal()
    })
    // 添加好友窗口的添加按钮事件
    $('#add_friend_confirm_btn').click(function () {
        name = $('#friend_name').val().trim()
        $.post({
            url: '/api/v1/friends',
            contentType: 'application/json',
            data: JSON.stringify({ name: name })
        }).done(function (res) {
            console.log('add friend: ', res);
            // location.href = location.pathname + '?tab=friend';
            $('#add_friend_modal').modal('hide')
            $('#friend_btn').click()
        });
    })
    // 点击好友列表的li进入对应的聊天室
    $('#friend_list').on('click', 'li', function () {
        friend_name = $(this).find('span').eq(0).text()
        friend_id = $(this).closest('li').attr('data')
        $.getJSON('/api/v1/friends/' + friend_id + '/chats', function (chats) {
            // 如果已经在聊天室，先发出离开聊天室信号
            if (ROOM) {
                socket.emit('leave_chatroom', { name: user_name, room: ROOM });
            }
            // 在页面上存储该好友信息
            $('.chatpnl').attr('data', friend_id)
            $('.chathead').text(friend_name)
            // 获取当前用户信息
            current_user_id = $('.user').attr('data')
            user_name = $('.user span').text()
            // 清空当前聊天区域
            $('.chat-content').empty()
            // 遍历获取的聊天记录，往聊天区域填充
            for (var i = 0; i < chats.length; i++) {
                chat = chats[i]
                div = '<div class="chat' + (chat.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
                    '                <div class="chat">\n' +
                    '                    <div class="chatinfo ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
                    '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
                    '                        <div>' + chat.sender_name + '</div>\n' +
                    '                    </div>\n' +
                    '                    <div class="chatcontent ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">' + chat.content + '</div>\n' +
                    '                    <div class="clear"></div>\n' +
                    '                </div>\n' +
                    '            </div>'
                $('.chat-content').append(div)
            }
            // 滑到最底部，查看最新的聊天内容
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            setTimeout(function () {
                $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            }, 100);
            // 设置全局变量
            ROOM = null
            FRIEND = friend_id
            // 显示editor
            $('#editor').show()
        })
    })

})
ROOM = null
FRIEND = null
var socket = io('http://' + location.hostname + ':' + location.port + '/websocket');
socket.on('connect', function () { // 发送到服务器的通信内容
    // socket.emit('join_chatroom', {name:'11',room: '1'});
});
socket.on('message', function (msg) {
    //显示接受到的通信内容，包括服务器端直接发送的内容和反馈给客户端的内容
    current_user_id = $('.user').attr('data')
    console.log('msg', msg)
    chat = JSON.parse(msg)
    console.log(chat)
    if (ROOM && chat.chatroom_id == ROOM) {
        if (chat.sender_name == 'admin') {
            div = '<div class="clear"></div>\n' +
                '            <div class="cahtnotice">\n' +
                '                <p>---------' + chat.content + '--------</p>\n' +
                '            </div>'
        } else {
            div = '<div class="chat' + (chat.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
                '                <div class="chat">\n' +
                '                    <div class="chatinfo ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
                '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
                '                        <div>' + chat.sender_name + '</div>\n' +
                '                    </div>\n' +
                '                    <div class="chatcontent ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">' + chat.content + '</div>\n' +
                '                    <div class="clear"></div>\n' +
                '                </div>\n' +
                '            </div>'
        }
    } else if (FRIEND && (chat.sender_id == FRIEND || chat.receiver_id == FRIEND)) {
        div = '<div class="chat' + (chat.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
            '                <div class="chat">\n' +
            '                    <div class="chatinfo ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
            '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
            '                        <div>' + chat.sender_name + '</div>\n' +
            '                    </div>\n' +
            '                    <div class="chatcontent ' + (chat.sender_id == current_user_id ? 'fr' : 'fl') + '">' + chat.content + '</div>\n' +
            '                    <div class="clear"></div>\n' +
            '                </div>\n' +
            '            </div>'
    }
    $('.chat-content').append(div)
    $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
});