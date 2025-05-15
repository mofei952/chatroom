$(function () {
    // 请求失败时的统一处理
    $(document).ajaxError(function (event, jqXHR, ajaxOptions, thrownError) {
        // 统一错误处理
        const errorResponse = jqXHR.responseJSON;
        if (errorResponse) {
            alert(errorResponse.message);
            return
        }
    });
    
    // 当前用户信息
    current_user_id = null
    current_user_name = null
    // 当前聊天对象信息
    current_chatroom_id = null
    current_friend_id = null
    // 默认头像url
    default_user_avatar = '/static/image/default_user_avatar.png'
    default_chatroom_avatar = '/static/image/default_chatroom_avatar.png'
    // 当前聊天窗口最老一条消息时间，用来加载更早的消息
    oldest_message_time = null
    // 当前聊天窗口最新一条消息时间和最新组内消息数量，用来在接收新消息时进行分组的判断
    newest_message_time = null
    newest_group_message_count = 0


    // 获取当前用户信息
    $.getJSON('/api/v1/users/me', function (user) {
        current_user_id = user.id
        current_user_name = user.name
        $('#current_user_name').text(user.nickname)
        $('#current_user_avatar').attr('src', user.avatar || default_user_avatar)
        $('#modify_information_modal #name').val(user.name)
        $('#modify_information_modal #nickname').val(user.nickname)
        $('#modify_information_modal #avatar').attr('src', user.avatar || default_user_avatar)
    })

    // 点击左上角个人信息卡片显示修改个人信息窗口
    $('.user').click(function () {
        $('#modify_information_modal').modal()
    })
    // 点击图片时触发文件选择
    $('#avatar').click(function() {
        $('#avatar_input').click();
    });
    // 文件选择变化时处理
    avatar_file = null
    $('#avatar_input').change(function(e) {
        if (this.files && this.files[0]) {
            avatar_file = this.files[0]
            var reader = new FileReader();
            reader.onload = function(e) {
                // 替换图片的src为选择的图片
                $('#avatar').attr('src', e.target.result);
            }
            // 读取图片文件为Data URL
            reader.readAsDataURL(this.files[0]);
        }
    });
    // 点击保存按钮时发送请求
    $('#modify_information_confirm_btn').click(function() {
        // 创建FormData对象
        var formData = new FormData();
        formData.append('avatar', avatar_file);
        
        // 可以添加其他表单数据
        formData.append('nickname', $('#nickname').val());
        
        // 显示加载状态
        $(this).prop('disabled', true).text('上传中...');
        
        // 发送AJAX请求
        $.ajax({
            url: '/api/v1/users/me',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                alert('图片上传成功！');
                console.log('服务器响应:', response);
            },
            error: function(xhr, status, error) {
                alert('图片上传失败: ' + error);
                console.error('上传错误:', error);
            },
            complete: function() {
                // 恢复按钮状态
                $('#modify_information_confirm_btn').prop('disabled', false).text('保存图片');
            }
        });
    });

    // 根据message对象生成消息div
    function get_message_div(message) {
        if (!message.sender_id) {
            div = '<div class="clear"></div>\n' +
                '            <div class="chatnotice">\n' +
                '                <p>' + message.content + '</p>\n' +
                '            </div>'
        } else if (message.is_recalled) {
            div = '<div class="clear"></div>\n' +
                '            <div class="chatnotice">\n' +
                '                <p>' + (message.sender_id == current_user_id ? '你' : message.sender_name) + '撤回了一条消息</p>\n' +
                '            </div>'
        } else {
            div = '<div class="chat' + (message.sender_id == current_user_id ? 'right' : 'left') + '">\n' +
                '                <div class="chat" data="' + message.id + '">\n' +
                '                    <div class="chatinfo ' + (message.sender_id == current_user_id ? 'fr' : 'fl') + '">\n' +
                '                        <img src="' + (message.sender_avatar || default_user_avatar) + '" alt="用户头像" class="avatar" title="用户名：' + message.sender_name + '"><br/>\n' +
                // '                        <div>' + (message.chatroom_id ? message.sender_nickname : '') + '</div>\n' +
                '                    </div>\n' +
                '                    <div class="chatcontainer">\n' + 
                '                        <div class="chatname">' + (message.chatroom_id ? message.sender_nickname : '') + '</div>\n' +
                '                        <div class="chatcontent">' + 
                                                message.content + 
                '                            <div class="action-buttons">' + (message.sender_id == current_user_id ? '<button class="recall-btn">撤回</button>' : "") +'</div>\n' + 
                '                        </div>\n' +
                '                    </div>\n' +
                '                    <div class="clear"></div>\n' +
                '                </div>\n' +
                '            </div>'
        }
        return div
    }
    // 计算两个时间字符串的分钟差
    function get_time_diff_in_minutes(time_str1, time_str2) {
        console.log(time_str1, time_str2)
        const date1 = new Date(time_str1.replace(' ', 'T'));
        const date2 = new Date(time_str2.replace(' ', 'T'));
        
        // 计算时间差（毫秒）并转换为分钟
        const diff_ms = Math.abs(date1 - date2);
        const diff_minutes = diff_ms / (1000 * 60);
        
        return diff_minutes;
    }
    // 在聊天窗口最前面插入消息列表
    function prepend_messages(messages, first=false) {
        // 如果是当前聊天窗口首次加载，则重置最新组内消息数量
        if (first) {
            newest_group_message_count = 0
        }
        if (messages.length == 0) {
            return
        }
        // 记录最老一条消息时间
        oldest_message_time = messages.at(-1).created_at
        // 如果是当前聊天窗口首次加载，则记录最新一条记录时间
        if (first) {
            newest_message_time = messages.at(0).created_at
        }
        // 插入消息前聊天窗口的高度和滚动条位置
        scroll_height_before = $('.chat-content').prop('scrollHeight')
        scroll_top_before = $('.chat-content').scrollTop()
        // 倒序插入消息列表
        group_message_count = 0
        for (var i = 0; i < messages.length; i++) {
            // 插入消息
            message = messages[i]
            div = get_message_div(message)
            $('.chat-content').prepend(div)
            // 组内消息加1
            group_message_count += 1
            // 如果是最后一条消息 或者 下一条消息在5分钟以外 或者 组内消息大于20，则插入一个时间节点
            next_message = messages[i+1]
            if (! next_message || get_time_diff_in_minutes(message.created_at, next_message.created_at) > 5 || group_message_count >= 20) {
                if (newest_group_message_count == 0) {
                    newest_group_message_count = group_message_count
                }
                group_message_count = 0
                $('.chat-content').prepend('<div class="clear"></div>\n' +
                               '            <div class="chatnotice">\n' +
                               '                <p class="chattime">' + message.send_time + '</p>\n' +
                               '            </div>'
                )
                
            }
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
                    '                <div class="room">\n' +
                    '                    <img src="' + default_chatroom_avatar + '" alt="聊天室" class="avatar">\n' +
                    '                    <span class="name">' + room.name + '</span>\n' +
                    '                    <div class="right">\n' + 
                    '                        <span class="label">' + (room.is_private ? '私密' : '') + '</span>\n' +
                    '                        <span class="time">' + room.last_active_time + '</span>\n' +
                    '                    </div>\n' +
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
        chatroom_name = $('#chatroom_name').val().trim()
        chatroom_type = $("input[name='chatroom_type']:checked").val();
        $.post({
            url: '/api/v1/chatrooms',
            contentType: 'application/json',
            data: JSON.stringify({ name: chatroom_name, is_private: chatroom_type == 'private' })
        }).done(function (res) {
            console.log('create chatroom: ', res);
            location.reload()
        });
    })
    // 点击聊天室列表的li进入对应的聊天室
    $('#room_list').on('click', 'li', function () {
        chatroom_name = $(this).find('span').eq(0).text()
        chatroom_id = $(this).closest('li').attr('data')
        label_text = $(this).closest('li').find('.label').text()
        // 请求接口查询聊天室最近的消息列表
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
            prepend_messages(messages, first=true)
            // 滑到最底部，查看最新的聊天内容
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            // 发出进入聊天室信号
            socket.emit('join_chatroom', { name: current_user_name, room: current_chatroom_id });
            // 显示editor并清空
            $('#editor').show()
            ue.setContent('')
            // 请求接口查询聊天室成员列表
            if(label_text == '私密') {
                $('.memberpnl').show()
                $.getJSON('/api/v1/chatrooms/' + chatroom_id + '/members', function (members) {
                    $('#member_list').empty()
                    for (var i = 0; i < members.length; i++) {
                        member = members[i]
                        li = '<li data="' + member.id + '">\n' +
                                '<div class="member">\n' +
                                    '<img src="' + (member.avatar || default_user_avatar) + '" alt="用户头像" class="avatar ' + (member.is_online ? '' : 'offline_avatar') + '">\n' +
                                    '<span class="name ' + (member.is_online ? '' : 'offline_username') + '">' + member.nickname + '</span>\n' +
                                '</div>\n' +
                            '</li>'
                        $('#member_list').append(li)
                    }
                })
            } else {
                $('.memberpnl').hide()
            }
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
                    '                <div class="room">\n' +
                    '                    <img src="' + (friend.avatar || default_user_avatar) + '" alt="用户头像" class="avatar ' + (friend.is_online ? '' : 'offline_avatar') + '">\n' +
                    '                    <div class="unread_mark" ' + (friend.unread_count ? '' : 'style="display: none;"') + '>' + friend.unread_count +'</div>\n' + 
                    '                    <span class="name ' + (friend.is_online ? '' : 'offline_username') + '">' + friend.nickname + '</span>\n' +
                    '                    <div class="right">\n' + 
                    '                        <span class="time">' + (friend.last_active_time || '') + '</span>\n' +
                    '                    </div>\n' +
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
    // 点击好友列表的li进入对应的聊天窗口
    $('#friend_list').on('click', 'li', function () {
        friend_name = $(this).find('span').eq(0).text()
        friend_id = $(this).closest('li').attr('data')
        unread_mark_div = $(this).find('.unread_mark')
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
            prepend_messages(messages, first=true)
            // 滑到最底部，查看最新的聊天内容
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
            // 显示editor
            $('#editor').show()
            // 隐藏成员列表div
            $('.memberpnl').hide()
            // 清空当前聊天窗口的未读标记
            clear_current_chat_unread_mark()
        })
    })

    // 初始化时模拟点击聊天室按钮或联系人按钮
    url_params = new URLSearchParams(window.location.search);
    if (url_params.get('tab') == 'friend') {
        $('#friend_btn').click()
    } else {
        $('#chatroom_btn').click()
    }
    
    // 初始化ueditor
    var ue = UE.getEditor('editor', {
        //这里可以选择自己需要的工具按钮名称,此处仅选择如下七个
        toolbars: [
            ['simpleupload', /*'insertimage',*/ 'emotion', 'scrawl']
        ],
        elementPathEnabled: false,
        initialFrameWidth: '100%',
        initialFrameHeight: 98,
        maximumWords: 100,
        wordOverFlowMsg: '<span style="color:red;">你输入的字符个数已经超出最大允许值！</span>',
        autoHeightEnabled: false,
        enableAutoSave: false,
        saveInterval: 86400000
    });
    // 清空当前聊天窗口的未读标记
    function clear_current_chat_unread_mark() {
        if ($('#friend_list').is(':visible') && current_friend_id) {
            li = $('#friend_list').find('li[data='+ current_friend_id +']')
            unread_mark_div = li.find('.unread_mark')
            if (unread_mark_div.is(':visible')) {
                friend_name = li.find('.name').text()
                $.post({
                    url: '/api/v1/friends/' + current_friend_id + '/read_markers',
                    contentType: 'application/json',
                }).done(function () {
                    console.log('将好友【' + friend_name + '】的消息标记为已读')
                    unread_mark_div.hide()
                });
            }
        }
    }
    // 在ueditor编辑中输入回车进行发送
    var domUtils = UE.dom.domUtils;
    ue.addListener('ready', function () {
        ue.focus(true);
        domUtils.on(ue.body, "click", function (event) {
            // 点击任意区域 清空当前聊天窗口的未读标记
            clear_current_chat_unread_mark()
        })
        domUtils.on(ue.body, "keydown", function (event) {
            // 按下任意键 清空当前聊天窗口的未读标记
            clear_current_chat_unread_mark()
            // 回车发送
            if (event.code == 'Enter') {
                event.preventDefault();
                event.stopPropagation();
                // 空白内容不发送
                text = ue.getContent()
                if (!text) {
                    return
                }
                // 去掉结尾的换行
                text = text.replace(/<br\/><\/p>$/i, '</p>')
                // 调用发送接口
                console.log('send')
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
    // 点击任意区域 清空当前聊天窗口的未读标记
    $(document).on('click', function() {
        clear_current_chat_unread_mark()
    });
        
    is_loading = false
    scroll_debounce_timer = null
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
            $.getJSON('/api/v1/chatrooms/' + current_chatroom_id + '/messages?before_time=' + oldest_message_time, function (messages) {
                prepend_messages(messages)
            }).always(function () {
                is_loading = false
            });
        } else {
            $.getJSON('/api/v1/friends/' + current_friend_id + '/messages?before_time=' + oldest_message_time, function (messages) {
                prepend_messages(messages)
            }).always(function () {
                is_loading = false
            });
        }
    }

    // 点击撤回按钮撤回消息
    $('.chat-content').on('click', '.recall-btn', function () {
        message_id = $(this).closest('.chat').attr('data')
        if (current_chatroom_id) {
            url = '/api/v1/chatrooms/' + current_chatroom_id + '/messages/' + message_id
        } else if (current_friend_id) {
            url = '/api/v1/friends/' + current_friend_id + '/messages/' + message_id
        }
        // 撤回消息
        $.ajax({
            url: url,
            type: 'DELETE',
            contentType: 'application/json',
        }).done(function (res) {
            console.log('recall message: ', message_id);
        });
    })

    invitation_link = null
    // 点击成员列表的+按钮显示创建邀请链接窗口
    $('#add_member_btn').click(function () {
        $('#invitation_link').text('')
        $('#add_member_confirm_btn').text('生成')
        $('#add_member_modal').modal()
    })
    // 创建邀请链接窗口的创建按钮事件
    $('#add_member_confirm_btn').click(function () {
        if($('#add_member_confirm_btn').text() == '生成') {
            valid_days = $('#valid_days').val()
            $.getJSON('/api/v1/chatrooms/' + current_chatroom_id + '/invitation_link?valid_days=' + valid_days, function (link) {
                invitation_link = link
                $('#invitation_link').text('邀请链接：\n' + link)
                $('#add_member_confirm_btn').text('复制')
            })
        } else {
            navigator.clipboard.writeText(invitation_link)
            .then(function() {
                alert("已复制到剪贴板！");
            })
            .catch(function(err) {
                alert("复制失败，请手动复制");
            });
        }
    })

    // 如果有join_token参数，请求join接口加入聊天室
    if (url_params.has('join_token')) {
        join_token = url_params.get('join_token')
        console.log(join_token)
        $.post({
            url: '/api/v1/chatrooms/join',
            contentType: 'application/json',
            data: JSON.stringify({ join_token: join_token })
        }).done(function (chatroom) {
            alert('成功加入聊天室【' + chatroom.name + '】')
            location.href = location.pathname;
        });
    }
    
    // websocket连接和事件监听
    var socket = io('http://' + location.hostname + ':' + location.port + '/websocket');
    socket.on('connect', function () {
        setInterval(send_heartbeat, 30000);
    });
    socket.on('json', function (message) {
        // 显示接受到的通信内容，包括服务器端直接发送的内容和反馈给客户端的内容
        console.log('receive: ', message)
        // 如果是第一条消息 或者 上一条消息在5分钟以外 或者 组内消息大于20，则插入一个时间节点
        if (! newest_message_time || get_time_diff_in_minutes(message.created_at, newest_message_time) > 5 || newest_group_message_count >= 20) {
            newest_group_message_count = 0
            $('.chat-content').append('<div class="clear"></div>\n' +
                '            <div class="chatnotice">\n' +
                '                <p class="chattime">' + message.send_time + '</p>\n' +
                '            </div>'
            )
        }
        // 更新最新消息时间和最新组内消息数
        newest_message_time = message.created_at
        newest_group_message_count += 1
        // 插入消息div
        if (current_chatroom_id && message.chatroom_id == current_chatroom_id) {
            div = get_message_div(message)
            $('.chat-content').append(div)
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
        } else if (current_friend_id && (message.sender_id == current_friend_id || message.receiver_id == current_friend_id)) {
            div = get_message_div(message)
            $('.chat-content').append(div)
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'));
        } 
    });
    socket.on('message_recalled', function (message) {
        console.log('receive recalled message: ', message)
        if (current_chatroom_id && message.chatroom_id == current_chatroom_id 
            ||  (current_friend_id && (message.sender_id == current_friend_id || message.receiver_id == current_friend_id))
        ) {
            chatright = $('.chat[data='+message.id+']').parent()
            div = get_message_div(message)
            chatright.after(div)
            chatright.remove()
        }
    })
    socket.on('unread_update', function (frinedship) {
        console.log('receive unread update: ', frinedship)
        // 如果在好友聊天页面，则更新好友列表的最近消息时间和未读数量
        if ($('#friend_list').is(':visible')) {
            li = $('#friend_list').find('li[data='+ frinedship.id +']')
            li.find('.time').text(frinedship.last_active_time)
            li.find('.unread_mark').text(frinedship.unread_count)
            li.find('.unread_mark').show()
        }
    })
    socket.on('user_online', function (data) {
        console.log('receive user online: ', data)
        // 如果在好友聊天页面，则更新好友的在线状态
        if ($('#friend_list').is(':visible')) {
            li = $('#friend_list').find('li[data='+ data.user_id +']')
            if (li) {
                li.find('.avatar').removeClass('offline_avatar')
                li.find('.name').removeClass('offline_username')
            }
        }
        // 如果成员列表可见，则更新成员的在线状态
        if ($('#member_list').is(':visible')) {
            li = $('#member_list').find('li[data='+ data.user_id +']')
            if (li) {
                li.find('.avatar').removeClass('offline_avatar')
                li.find('.name').removeClass('offline_username')
            }
        }
    })
    socket.on('user_offline', function (data) {
        console.log('receive user offline: ', data)
        // 如果在好友聊天页面，则更新好友的在线状态
        if ($('#friend_list').is(':visible')) {
            user_ids = data['user_ids']
            for (var i = 0; i < user_ids.length; i++) {
                user_id = user_ids[i]
                li = $('#friend_list').find('li[data='+ user_id +']')
                if (li) {
                    li.find('.avatar').addClass('offline_avatar')
                    li.find('.name').addClass('offline_username')
                }
            }                
        }
        // 如果成员列表可见，则更新成员的在线状态
        if ($('#member_list').is(':visible')) {
            user_ids = data['user_ids']
            for (var i = 0; i < user_ids.length; i++) {
                user_id = user_ids[i]
                li = $('#member_list').find('li[data='+ user_id +']')
                if (li) {
                    li.find('.avatar').addClass('offline_avatar')
                    li.find('.name').addClass('offline_username')
                }
            }                
        }
    })
    // 发送心跳
    function send_heartbeat() {
        if (socket.connected) {
            console.log('send heartbeat')
            socket.emit('heartbeat');
        }
    }
    // 标签页关闭时断开连接
    window.addEventListener('beforeunload', () => {
        if (socket.connected) {
          // 设置超时强制断开
          setTimeout(() => {
            if (socket.connected) socket.close();
          }, 100);
          socket.disconnect();
        }
      });
})


