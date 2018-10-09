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
                chat_room_id = $('.chatpnl').attr('data')
                $.post('/chat_room_send/'+chat_room_id, {content: text}, function (res) {
                    if (res == 'true'){
                        // chatDiv = '<div class="chatright">\n' +
                        //     '                <div class="chat">\n' +
                        //     '                    <img src="/static/image/user.png" alt="用户头像" class="chaticon fr">\n' +
                        //     '                    <p class="fr">' + text + '</p>\n' +
                        //     '                    <div class="clear"></div>\n' +
                        //     '                </div>\n' +
                        //     '            </div>'
                        // $('.chat-content').append(chatDiv)
                        $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
                        ue.setContent('')
                    }else{
                        alert('发送失败')
                    }
                }, 'json')
            }
        })
    });

    // 点击聊天室按钮显示聊天室列表
    $('#chat_room_btn').click(function () {
        $.getJSON('/get_chat_room_list', function (chat_rooms) {
            $('.chatlist').empty()
            for (var i = 0; i < chat_rooms.length; i++){
                chat_room = chat_rooms[i]
                console.log(chat_room)
                li = '<li data="'+chat_room.id+'">\n' +
                    '                <div class="qun">\n' +
                    '                    <img src="/static/image/user.png" alt="用户头像" class="qunicon">\n' +
                    '                    <span>'+chat_room.name+'</span>\n' +
                    '                    <span class="time">12:08</span>\n' +
                    '                </div>\n' +
                    '            </li>'
                $('.chatlist').append(li)
            }

        })
    })
    // 点击聊天室按钮显示聊天室列表
    $('#add_chat_room_btn').click(function () {
        $('#myModal').modal()
    })
    // 创建聊天室窗口的创建按钮事件
    $('#create_btn').click(function () {
        name = $('#chat_room_name').val().trim()
        $.post('/create_chat_room', {name: name, csrf_token: $('#csrf_token').val()}, function (res) {
            if(res == 'true'){
                location.reload()
            }
        }, 'json')
    })
    // 点击聊天室列表的li进入对应的聊天室
    $('.chatlist').on('click', 'li', function () {
        chat_room_name = $(this).find('span').eq(0).text()
        chat_room_id = $(this).closest('li').attr('data')
        $.getJSON('/get_chat_list/'+chat_room_id, function (chats) {
            // 在页面上存储该聊天室信息，
            $('.chatpnl').attr('data', chat_room_id)
            $('.chathead').text(chat_room_name)
            // 获取当前用户信息
            current_user_id = $('.user').attr('data')
            user_name = $('.user span').text()
            // 清空当前聊天区域
            $('.chat-content').empty()
            // 遍历获取的聊天记录，往聊天区域填充
            for(var i = 0; i < chats.length; i++){
                chat = chats[i]
                div = '<div class="chat'+(chat.sender_id == current_user_id ? 'right' : 'left')+'">\n' +
                    '                <div class="chat">\n' +
                    '                    <div class="chatinfo '+(chat.sender_id == current_user_id ? 'fr' : 'fl')+'">\n' +
                    '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
                    '                        <div>'+chat.sender_name+'</div>\n' +
                    '                    </div>\n' +
                    '                    <div class="chatcontent '+(chat.sender_id == current_user_id ? 'fr' : 'fl')+'">'+chat.content+'</div>\n' +
                    '                    <div class="clear"></div>\n' +
                    '                </div>\n' +
                    '            </div>'
                $('.chat-content').append(div)
            }
            // 滑到最底部，查看最新的聊天内容
            $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
            // 如果已经在聊天室，先发出离开聊天室信号
            if(room){
                socket.emit('leave_chat_room', {name: user_name, room: room});
            }
            // 发出进入聊天室信号
            socket.emit('join_chat_room', {name: user_name, room: chat_room_id});
            room = chat_room_id
            // 显示editor
            $('#editor').show()
        })
    })

    // 点击联系人按钮显示好友列表
    $('#friend_btn').click(function () {
        alert('未实现')
        $.getJSON('/get_friend_list', function (friends) {
            $('.chatlist').empty()
            $('.chatlist').append('<li>\n' +
                    '                <div class="qun">\n' +
                    '                    <img src="/static/image/user.png" alt="用户头像" class="qunicon">\n' +
                    '                    <span>'+'xxx'+'</span>\n' +
                    '                    <span class="time">12:08</span>\n' +
                    '                </div>\n' +
                    '            </li>')
            for (var i = 0; i < friends.length; i++){
                friend = friends[i]
                $('.chatlist').append('<li>\n' +
                    '                <div class="qun">\n' +
                    '                    <img src="/static/image/user.png" alt="用户头像" class="qunicon">\n' +
                    '                    <span>'+friend.name+'</span>\n' +
                    '                    <span class="time">12:08</span>\n' +
                    '                </div>\n' +
                    '            </li>')
            }
        })
    })
})
room = null
var socket = io('http://'+location.hostname+':'+location.port+'/websocket');
socket.on('connect', function() { // 发送到服务器的通信内容
    // socket.emit('join_chat_room', {name:'11',room: '1'});
});
socket.on('message', function(msg) {
    //显示接受到的通信内容，包括服务器端直接发送的内容和反馈给客户端的内容
    current_user_id = $('.user').attr('data')
    console.log('msg',msg)
    chat = JSON.parse(msg)
    console.log(chat)
    if(chat.sender_name == 'admin'){
        div='<div class="clear"></div>\n' +
        '            <div class="cahtnotice">\n' +
        '                <p>---------'+chat.content+'--------</p>\n' +
        '            </div>'
    }else{
        div = '<div class="chat'+(chat.sender_id == current_user_id ? 'right' : 'left')+'">\n' +
        '                <div class="chat">\n' +
        '                    <div class="chatinfo '+(chat.sender_id == current_user_id ? 'fr' : 'fl')+'">\n' +
        '                        <img src="/static/image/user.png" alt="用户头像" class="chaticon"><br/>\n' +
        '                        <div>'+chat.sender_name+'</div>\n' +
        '                    </div>\n' +
        '                    <div class="chatcontent '+(chat.sender_id == current_user_id ? 'fr' : 'fl')+'">'+chat.content+'</div>\n' +
        '                    <div class="clear"></div>\n' +
        '                </div>\n' +
        '            </div>'
    }
    $('.chat-content').append(div)
    $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
});