$(function () {
    // 当前用户信息
    current_user_id = $('.user').attr('data')
    current_user_name = $('.user span').text()
    // 当前聊天对象信息
    current_chatroom_id = null
    current_friend_id = null

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
                console.log('send')
                text = ue.getContent()
                if (current_chatroom_id) {
                    $.post('/api/v1/chatrooms/' + current_chatroom_id + '/messages', { content: text }, function (res) {
                        $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
                        ue.setContent('')
                    }, 'json')
                } else if (current_friend_id) {
                    $.post('/api/v1/friends/' + current_friend_id + '/messages', { content: text }, function (res) {
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

    // 在聊天窗口最前面插入消息列表
    function prepend_messages(messages) {
        // 插入消息前聊天窗口的高度和滚动条位置
        scroll_height_before = $('.chat-content').prop('scrollHeight')
        scroll_top_before = $('.chat-content').scrollTop()
        // 插入消息列表
        for (var i = 0; i < messages.length; i++) {
            message = messages[i]
            div = '<div class="chat' + (message.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
                '                <div class="chat">\n' +
                '                    <div class="chatinfo ' + (message.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
                '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
                '                        <div>' + message.sender_name + '</div>\n' +
                '                    </div>\n' +
                '                    <div class="chatcontent ' + (message.sender_id == current_user_id ? 'fr' : 'fl') + '">' + message.content + '</div>\n' +
                '                    <div class="clear"></div>\n' +
                '                </div>\n' +
                '            </div>'
            $('.chat-content').prepend(div)
        }
        // 插入消息后聊天窗口的高度
        scroll_height_after = $('.chat-content').prop('scrollHeight')
        // 保持滚动位置
        $('.chat-content').scrollTop(scroll_height_after - scroll_height_before + scroll_top_before);
    }

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
        $.getJSON('/api/v1/chatrooms/' + chatroom_id + '/messages', function (messages) {
            // 如果已经在聊天室，先发出离开聊天室信号
            if (current_chatroom_id) {
                socket.emit('leave_chatroom', { name: current_user_name, room: current_chatroom_id });
            }
            // 修改当前聊天对象信息
            current_chatroom_id = chatroom_id
            curretn_friend_id = null
            // 在页面上存储该聊天室信息
            $('.chatpnl').attr('data', current_chatroom_id)
            $('.chathead').text(chatroom_name)
            // 清空当前聊天区域
            $('.chat-content').empty()
            // 遍历获取的聊天记录，往聊天区域填充
            prepend_messages(messages)
            // 记录最后一条消息的时间
            if (messages.length != 0) {
                last_message_time = messages.at(-1).created_at
            }
            // 滑到最底部，查看最新的聊天内容
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            // 发出进入聊天室信号
            socket.emit('join_chatroom', { name: current_user_name, room: current_chatroom_id });
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
        $.getJSON('/api/v1/friends/' + friend_id + '/messages', function (messages) {
            // 如果已经在聊天室，先发出离开聊天室信号
            if (current_chatroom_id) {
                socket.emit('leave_chatroom', { name: current_user_name, room: current_chatroom_id });
            }
            // 修改当前聊天对象信息
            current_chatroom_id = null
            current_friend_id = friend_id
            // 在页面上存储该好友信息
            $('.chatpnl').attr('data', current_friend_id)
            $('.chathead').text(friend_name)
            // 清空当前聊天区域
            $('.chat-content').empty()
            // 遍历获取的聊天记录，往聊天区域填充
            prepend_messages(messages)
            // 记录最后一条消息的时间
            if (messages.length != 0) {
                last_message_time = messages.at(-1).created_at
            }
            // 滑到最底部，查看最新的聊天内容
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            // 显示editor
            $('#editor').show()
        })
    })

    is_loading = false
    scroll_debounce_timer = null
    last_message_time = null
    // 滑动到聊天框顶部时加载更早之前的聊天记录
    $('.chat-content').on('scroll', function () {
        clearTimeout(scroll_debounce_timer);
        scroll_debounce_timer = setTimeout(function () {
            // 判断是否接近顶部（距离顶部 < 50px）
            if ($('.chat-content').scrollTop() < 50 && !is_loading) {
                load_more_message();
            }
        }, 100); // 防抖延迟100ms
    });
    function load_more_message() {
        is_loading = true
        if (current_chatroom_id) {
            $.getJSON('/api/v1/chatrooms/' + current_chatroom_id + '/messages?last_message_time=' + last_message_time, function (messages) {
                if (messages.length > 0) {
                    prepend_messages(messages)
                    last_message_time = messages.at(-1).created_at
                }
            }).always(function () {
                is_loading = false
            });
        } else {
            $.getJSON('/api/v1/friends/' + current_friend_id + '/messages?last_message_time=' + last_message_time, function (messages) {
                if (messages.length > 0) {
                    prepend_messages(messages)
                    last_message_time = messages.at(-1).created_at
                }
            }).always(function () {
                is_loading = false
            });
        }
    }

})

var socket = io('http://' + location.hostname + ':' + location.port + '/websocket');
socket.on('connect', function () { // 发送到服务器的通信内容
    // socket.emit('join_chatroom', {name:'11',room: '1'});
});
socket.on('json', function (message) {
    //显示接受到的通信内容，包括服务器端直接发送的内容和反馈给客户端的内容
    console.log('receive: ', message)
    if (current_chatroom_id && message.chatroom_id == current_chatroom_id) {
        if (message.sender_name == 'admin') {
            div = '<div class="clear"></div>\n' +
                '            <div class="cahtnotice">\n' +
                '                <p>---------' + message.content + '--------</p>\n' +
                '            </div>'
        } else {
            div = '<div class="chat' + (message.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
                '                <div class="chat">\n' +
                '                    <div class="chatinfo ' + (message.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
                '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
                '                        <div>' + message.sender_name + '</div>\n' +
                '                    </div>\n' +
                '                    <div class="chatcontent ' + (message.sender_id == current_user_id ? 'fr' : 'fl') + '">' + message.content + '</div>\n' +
                '                    <div class="clear"></div>\n' +
                '                </div>\n' +
                '            </div>'
        }
    } else if (current_friend_id && (message.sender_id == current_friend_id || message.receiver_id == current_friend_id)) {
        div = '<div class="chat' + (message.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
            '                <div class="chat">\n' +
            '                    <div class="chatinfo ' + (message.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
            '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
            '                        <div>' + message.sender_name + '</div>\n' +
            '                    </div>\n' +
            '                    <div class="chatcontent ' + (message.sender_id == current_user_id ? 'fr' : 'fl') + '">' + message.content + '</div>\n' +
            '                    <div class="clear"></div>\n' +
            '                </div>\n' +
            '            </div>'
    }
    $('.chat-content').append(div)
    $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
});