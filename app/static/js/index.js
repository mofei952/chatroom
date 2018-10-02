$(function () {
    var ue = UE.getEditor('editor', {
        //这里可以选择自己需要的工具按钮名称,此处仅选择如下七个
        toolbars: [
            ['simpleupload', 'insertimage', 'emotion', 'scrawl']
        ],
        elementPathEnabled: false,
        initialFrameHeight: 98,
        maximumWords: 100,
        wordOverFlowMsg: '<span style="color:red;">你输入的字符个数已经超出最大允许值！</span>',
        autoHeightEnabled: false
    });
    var timer;
    var domUtils = UE.dom.domUtils;
    ue.addListener('ready', function () {
        ue.focus(true);
        domUtils.on(ue.body, "keydown", function (event) {
            if (event.code == 'Enter') {
                event.preventDefault();
                // event.stopPropagation()
                console.log('发送')
                text = ue.getContentTxt()
                chatDiv = '<div class="chatright">\n' +
                    '                <div class="chat">\n' +
                    '                    <img src="/static/image/user.png" alt="用户头像" class="chaticon fr">\n' +
                    '                    <p class="fr">' + text + '</p>\n' +
                    '                    <div class="clear"></div>\n' +
                    '                </div>\n' +
                    '            </div>'
                $('.chat-content').append(chatDiv)
                $('.chat-content').scrollTop($('.chat-content').prop('scrollHeight'))
                ue.setContent('')
            }
        })
    });
    $('#chat_room_btn').click(function () {
        console.log('chat')
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
    $('#friend_btn').click(function () {
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
    $('.chatlist').on('click', 'li', function () {
        console.log($(this).find('span').eq(0).text())
        chat_room_id = $(this).closest('li').attr('data')
        $.getJSON('/get_chat_list/'+chat_room_id, function (chats) {
            console.log(chats)
            $('.chat-content').empty()
            for(var i = 0; i < chats.length; i++){
                chat = chats[i]
                div = '<div class="chat'+(chat.sender_id == 1 ? 'right' : 'left')+'">\n' +
                    '                <div class="chat">\n' +
                    '                    <img src="/static/image/user.png" alt="用户头像" class="chaticon '+(chat.sender_id == 1 ? 'fr' : 'fl')+'">\n' +
                    '                    <p class="'+(chat.sender_id == 1 ? 'fr' : 'fl')+'">'+chat.content+'</p>\n' +
                    '                    <div class="clear"></div>\n' +
                    '                </div>\n' +
                    '            </div>'
                $('.chat-content').append(div)
            }
        })
    })
})