let socket = io.connect("http://" + location.host + "/ide/sock/");
const body = $("body");
const output = $("#output");
const $tree = $("#tree");
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) { return new bootstrap.Tooltip(tooltipTriggerEl); });
$('[data-bs-toggle="tooltip"]').on('click', function () { setTimeout(() => { $(this).tooltip('hide'); }, 100); });

//https://cdnjs.com/libraries/ace/1.9.6
const editor = ace.edit("editor");
var langTools = ace.require("ace/ext/language_tools");
editor.setTheme("ace/theme/tomorrow_night_bright");
editor.setFontSize("14px");
editor.session.setTabSize(4);
editor.setHighlightActiveLine(true);
editor.setShowPrintMargin(false);
editor.setOptions({copyWithEmptySelection: false, showGutter: true, showLineNumbers: true, enableBasicAutocompletion: false, enableSnippets: false, enableLiveAutocompletion: false});

$('#line').text(editor.getCursorPosition().row + 1);
$('#col').text(editor.getCursorPosition().column + 1);

// 코드 편집기에서 입력 시
editor.on('input', function(delta) {
    var cursorPos = editor.getCursorPosition();
    $('#line').text(cursorPos.row + 1);
    $('#col').text(cursorPos.column + 1);

    const treenode = $tree.jstree(true).get_selected(true);
    try {
        $(`#tab-${treenode[0].id}-name`).addClass('em');
        $(`#${treenode[0].id}_anchor`).addClass('em');
    }
    catch {}
});

// 파일 업로드 시
function openFile(e) {
    if (!editor.getReadOnly()) {
        try {
            const reader = new FileReader();
            reader.onload = function(event) { editor.setValue(event.target.result, 1); }   
            reader.readAsText(e.files[0]);
        } catch {}
    }
};

// 코드 저장 시
function saveFile() {
    const treenode = $tree.jstree(true).get_selected(true);
    if (treenode.length > 0) {
        if (treenode[0].type == 'file') {
            socket.emit("save", {id:treenode[0].id, file:treenode[0].text, path:getParentsById(treenode[0].id), code:editor.getValue()});
        }
    }
}

// 코드 다운로드 시
function downloadFile() {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(editor.getValue()));
    // element.setAttribute('download', `${getDateTimeAsString()}.py`);
    element.setAttribute('download', 'main.py');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

function getDateTimeAsString() {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, "0");
    const day = now.getDate().toString().padStart(2, "0");
    const hours = now.getHours().toString().padStart(2, "0");
    const minutes = now.getMinutes().toString().padStart(2, "0");
    const seconds = now.getSeconds().toString().padStart(2, "0");
    const formattedTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    return formattedTime;
}

// 테마 토글 버튼 클릭 시
$("#theme-toggle").on('click', function() {
    body.toggleClass('dark');

    if (body.hasClass('dark')) {
        $("#theme-icon").removeClass('fa-moon');
        $("#theme-icon").addClass('fa-sun');
        $tree.jstree("set_theme","default-dark");
        editor.setTheme("ace/theme/tomorrow_night_bright");
    } else {
        $("#theme-icon").removeClass('fa-sun');
        $("#theme-icon").addClass('fa-moon');
        $tree.jstree("set_theme","default");
        editor.setTheme("ace/theme/textmate");
    }
});

// 설정 모달 클릭 시
function showModal() { $("#settingModal").modal('show'); }
function closeModal() { $("#settingModal").modal('hide'); }

// 에디터 설정 값 변경 시
$("#setting-font").on('input', function() { editor.setFontSize($(this).val() + "px"); });
$("#setting-tab").on('input', function() { editor.session.setTabSize($(this).val()); });
$("#setting-highlight").change(function() { editor.setHighlightActiveLine(this.checked); });
$("#setting-gutter").change(function() { editor.setOptions({showGutter: this.checked}); });
$("#setting-linenumber").change(function() { editor.setOptions({showLineNumbers: this.checked}); });
$("#setting-autocompletion").change(function() { editor.setOptions({enableBasicAutocompletion: this.checked, enableSnippets: this.checked, enableLiveAutocompletion: this.checked}); });

function stopToRun() { // 중지 버튼에서 실행 버튼으로 변환
    $("#btn-run-icon").removeClass('fa-stop');
    $("#btn-run-icon").addClass('fa-play');
    $("#btn-run").removeClass('btn-danger');
    $("#btn-run").addClass('btn-success');
    $("#btn-run-text").text("RUN");
}

function runToStop() { // 실행 버튼에서 중지 버튼으로 변환
    output.empty();
    $("#btn-run-icon").removeClass('fa-play');
    $("#btn-run-icon").addClass('fa-stop');
    $("#btn-run").removeClass('btn-success');
    $("#btn-run").addClass('btn-danger');
    $("#btn-run-text").text("STOP");
}

function runCode(target_lang) {
    if ($("#btn-run").hasClass('btn-danger')) { // 코드 중지하기
        socket.emit("stop", {});
    } else { // 코드 실행하기
        const treenode = $tree.jstree(true).get_selected(true);
        if (treenode.length > 0) {
            if (treenode[0].type == 'file') {
                socket.emit("save", {id:treenode[0].id, file:treenode[0].text, path:getParentsById(treenode[0].id), code:editor.getValue()});
            }
        }
    }
}

function runCommand() {
    socket.emit("command", {command:$("#input-command").val()});
    $("#input-command").val('');
}

function openTerminal(target_lang) {
    output.empty();
    socket.emit("terminal", {lang:target_lang});
    $("#input-command").val('');
}

function copyOutput() {
    output.select();
    document.execCommand("copy");
    window.getSelection().removeAllRanges();

    $("#btn-copy").attr('data-bs-original-title', 'Copied!').tooltip('show');
    $("#btn-copy").attr('data-bs-original-title', 'Copy output');
}

// 소켓
// socket 접속 성공 시
socket.on("connect", function() { socket.emit("join", {}); });
socket.on("disconnect", function(data) { console.log("fail"); });
socket.on('redirect', function (data) { window.location = data.url; });
socket.on("join", function(data) {
    if (data.exit_code == 0) {
        const tree_data = JSON.parse(data.output);
        $tree.jstree(true).settings.core.data = tree_data;
        $tree.jstree(true).refresh();
        editor.setValue('Select a file from the directory structure on the left or click the + button at the top.\r\n\r\nYou cannot use the same file name in the same directory.');
        editor.setReadOnly(true);
    }
});
socket.on("run", function(data) {
    // console.log(data);
    if (data.exit_code == 0) {
        stopToRun();
        output.text(output.text() + "** Exit Code **\r\n");
    } else {
        output.text(output.text() + data.output);
        output.scrollTop(output[0].scrollHeight);
    }
});
socket.on("save", function(data) {
    if (data.exit_code == 0) {
        $(`#tab-${data.id}-name`).removeClass('em');
        $(`#${data.id}_anchor`).removeClass('em');

        runToStop();
        const treenode = $tree.jstree(true).get_node(data.id);
        socket.emit("run", {id:treenode.id, file:treenode.text, path:getParentsById(treenode.id)});
    } else {
        alert(d.output);
    }
});

///////////////////////////// jstree
// https://mine-it-record.tistory.com/375

$tree.jstree({
    'plugins': ['types', 'dnd', 'contextmenu', 'sort', 'unique', 'themes', 'state'],
    'core': {
        'themes':{
            'name':'default-dark',
            'icons':true,
            'dots':true
        },
        'check_callback': function(operation, node, node_parent, node_position, more) {
            // Node name    : node.text
            // Node parent  : node_parent.text
            // Node type    : node.type
            if (operation == "create_node") {
                if (node_parent.type == 'file') return false;
            }
            else if (operation === "move_node") {
                if (node_parent.id == '#') return false;
            }
            else if (operation == "delete_node") {
                var confirmDelete = confirm(`Are you sure to delete ${node.text}?`);
                if (!confirmDelete) return false;
                
                socket.emit("delete", {id:node.id, file:node.text, path:getParentsById(node.id)});
                return true;
            }
            else if (operation == "rename_node") {
                // Node old name : node.text
                // Node new name : node_position
                if (node.text == node_position) return false;

                let r = true;
                const p = $tree.jstree(true).get_node(node.parent);
                for(let i=0;i<p.children.length;i++){
                    if (p.children[i] != node.id) {
                        if ($tree.jstree(true).get_node(p.children[i]).text == node_position) {
                            r = false;
                            break;
                        }
                    }
                }
                if (!r) return false;
                $(`#tab-${node.id}-name`).text(node_position);
                return true;
            }
            return true;
        },
    },
    'types': {
        "directory": {
            'icon': '/static/css/jstree/folder.png',//'jstree-folder', //'fas fa-folder-open fa-xs m-2'
        },
        "file": {
            "icon": '/static/css/jstree/file.png',//'jstree-file', //'fas fa-file fa-xs m-2',
            "valid_children": []
        }
    },
    "contextmenu": {
        "items": function ($node) {
            var tree = $tree.jstree(true);
            return {
                "Create": {
                    "separator_before": false,
                    "separator_after": true,
                    "label": "Create",
                    "action": false,
                    "submenu": {
                        "File": {
                            "seperator_before": false,
                            "seperator_after": false,
                            "label": "File",
                            action: function (obj) {
                                $node = tree.create_node($node, { text: 'Untitled.py', type: 'file' });
                                tree.deselect_all();
                                tree.select_node($node);
                            }
                        },
                        "Directory": {
                            "seperator_before": false,
                            "seperator_after": false,
                            "label": "Directory",
                            action: function (obj) {
                                $node = tree.create_node($node, { text: 'directory', type: 'directory' });
                                tree.deselect_all();
                                tree.select_node($node);
                            }
                        }
                    }
                },
                "Rename": {
                    "separator_before": false,
                    "separator_after": false,
                    "label": "Rename",
                    "action": function (obj) {
                        tree.edit($node);                                    
                    }
                },
                "Remove": {
                    "separator_before": false,
                    "separator_after": false,
                    "label": "Remove",
                    "action": function (obj) {
                        tree.delete_node($node);
                    }
                }
            };
        }
    }
});

function addTab(ti) {
    const treenode =  $tree.jstree().get_node(ti);
    $('.tab').removeClass('active');
    if ($(`#tab-${ti}`).length == 0) {
        $('.add-tab').before(
            $(
            '<div class="tab active d-flex justify-content-between align-items-center" onclick="tabClick(this)" id="tab-'+ti+'"> \
                <span id="tab-'+ti+'-name">'+treenode.text+'</span> \
                <div class="tab-close rounded-circle d-flex justify-content-center align-items-center" onclick="tabClose(\''+ti+'\')"> \
                    <i class="fa-solid fa-xmark"></i> \
                </div> \
            </div>'
            )
        );
    }
    else {
        $(`#tab-${ti}`).addClass('active');
    }
}

function getParentsById(ni) {
    const treenode = $tree.jstree(true).get_node(ni);
    const p = Array();
    for (let i = treenode.parents.length - 2; i >= 0; i--) p.push($tree.jstree(true).get_node(treenode.parents[i]).text);
    return p;
}

/*********** create node ***********/
// request
$tree.on('create_node.jstree', function (e, d) {
    socket.emit("create", {id:d.node.id, file:d.node.text, type:d.node.type, path:getParentsById(d.node.id)});
});
// response
socket.on("create", function(d) {
    if (d.exit_code == 0) {
        const treenode = $tree.jstree(true).get_node(d.id);
        if (treenode.type == "file") {
            socket.emit("content", {id:d.id, file:treenode.text, path:getParentsById(d.id)});
            $tree.jstree(true).deselect_all();
            $tree.jstree(true).select_node(d.id);
        }
    } else {
        $tree.jstree(true).delete_node(d.id);
        alert(d.output);
    }
});
/***********************************/
/*********** select node ***********/
// request
$tree.on('select_node.jstree', function (e, d) {
    try {
        // 파일 좌클릭 시 콜백 함수 호출
        if (d.event.type == "click" && d.node.type === 'file') socket.emit("content", {id:d.node.id, file:d.node.text, path:getParentsById(d.node.id)});
    } catch {}
});
// response
socket.on('content', function(d) {
    if (d.exit_code == 0) {
        addTab(d.id);
        editor.setReadOnly(false);
        editor.setValue(d.output);
    } else {
        alert(d.output);
    }
});
/***********************************/
/*********** rename node ***********/
// request
$tree.on('rename_node.jstree', function (e, d) {
    if (d.old != d.text) socket.emit("rename", {id:d.node.id, file:[d.old, d.text], path:getParentsById(d.node.id)});
});
// response
socket.on('rename', function(d) {
    if (d.exit_code != 0) {
        location.reload();
        alert(d.output);
    }
});
/***********************************/
/*********** delete node ***********/
// response
socket.on('delete', function(d) {
    if (d.exit_code == 0) {
        tabClose(d.id);
    } else {
        alert(d.output);
    }
});
/***********************************/
/************ move node ************/
// request
$tree.on('move_node.jstree', function (e, d) {
    const sp = getParentsById(d.old_parent);
    const dp = getParentsById(d.node.id);
    sp.push($tree.jstree(true).get_node(d.old_parent).text);
    socket.emit("move", {id:d.node.id, file:d.node.text, path:[sp, dp]});
});
// response
socket.on('move', function(d) {
    if (d.exit_code != 0) {
        alert(d.output);
        location.reload();
    }
});
/***********************************/

/////////////////////////////
$('.add-tab').on('click', function (e) {
    let target_node_id;
    let current_node = $tree.jstree('get_selected', false);
    
    if (current_node.length == 0) {
        const root_node = $tree.jstree(true).get_node('#');
        const children = root_node.children[0];
        current_node = $tree.jstree(true).get_node(children).id;
    }
    else {
        current_node = current_node[0];
    }
    
    const treenode = $tree.jstree(true).get_node(current_node);
    if (treenode.type == 'file') target_node_id = treenode.parent;
    else target_node_id = current_node;

    $tree.jstree().create_node(target_node_id, {'text':'Untitled.py', 'type':'file'}, 'last');
});
function tabClick(obj) {
    $('.tab').removeClass('active');
    $(obj).addClass('active');
};
function tabClose(ti) {
    let p;
    if ($(`#tab-${ti}`).prev('.tab').length > 0) p = $(`#tab-${ti}`).prev('.tab').attr('id');
    else if ($(`#tab-${ti}`).next('.tab').length > 0) p = $(`#tab-${ti}`).next('.tab').attr('id');
    if (p) {
        const treenode = $tree.jstree(true).get_node(p.slice(4));
        $tree.jstree(true).deselect_all();
        $tree.jstree(true).select_node(treenode);
        socket.emit("content", {id:treenode.id, file:treenode.text, path:getParentsById(treenode.id)});
    } else {
        editor.setReadOnly(true);
        editor.setValue('');
    }
    $(`#tab-${ti}`).remove();
};