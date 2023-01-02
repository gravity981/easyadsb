import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    signal cancel
    signal confirmed(string txt)

    function open(title, txt) {
        titleText.text = title
        textField.text = txt 
        textField.focus = true
        textField.cursorPosition = textField.length
        visible = true
    }

    function close() {
        textField.text = ""
        visible = false
    }

    QtObject {
        id: internal
        readonly property int kfDefault: 0
        readonly property int kfShift: 1
        readonly property int kfBackspace: 2
        readonly property int kfAlt: 3
        readonly property int kfNumber: 4
        readonly property int kfEnter: 5
        readonly property int kfCancel: 6

        property bool isShift: false
        property bool isNum: false
        property bool isAlt: false
        property var keys: [
            [
                {txt: "q", num: "1", alt:"["},
                {txt: "w", num: "2", alt:"]"},
                {txt: "e", num: "3", alt:"{"},
                {txt: "r", num: "4", alt:"}"},
                {txt: "t", num: "5", alt:"#"},
                {txt: "z", num: "6", alt:"%"},
                {txt: "u", num: "7", alt:"^"},
                
            ],
            [
                {txt: "i", num: "8", alt:"*"},
                {txt: "o", num: "9", alt:"+"},
                {txt: "p", num: "0", alt:"="},
                {txt: "a", num: "-", alt:"_"},
                {txt: "s", num: "/", alt:"\\"},
                {txt: "d", num: ":", alt:"|"},
                {txt: "f", num: ";", alt:"~"},
                

            ],
            [
                {txt: "g", num: "(", alt:"<"},
                {txt: "h", num: ")", alt:">"},
                {txt: "j", num: "€", alt:"$"},
                {txt: "k", num: "&", alt:"°"},
                {txt: "l", num: "@", alt:""},
                {txt: "y", num: "\"", alt:""},
                {txt: "x", num: ".", alt:""},
                
            ],
            [
                {txt: "shift", func: internal.kfShift, span: 2},
                {txt: "c", num: ",", alt:""},
                {txt: "v", num: "?", alt:""},
                {txt: "b", num: "!", alt:""},
                {txt: "n", num: "`", alt:""},
                {txt: "m", num: "'", alt:""},
                
            ],
            [
                {txt: "nr", func: internal.kfNumber, span: 1},
                {txt: " ", span: 5},
                {txt: "<", func: internal.kfBackspace, span: 1},
            ],
            [
                {txt: "alt", func: internal.kfAlt, span: 1},
                {txt: "cancel", func: internal.kfCancel, span: 3},
                {txt: "enter", func: internal.kfEnter, span: 3},
            ]
        ]

        function keyPressed(func, txt, isLongPressed) {
            if (func === undefined) {
                func = internal.kfDefault
            }
            switch(func) {
                case internal.kfDefault:
                    isLongPressed ? keyboardController.onKeyLongPressed(textField, txt) : keyboardController.onKeyPressed(textField, txt)
                    break
                case internal.kfBackspace:
                    isLongPressed ? keyboardController.onKeyLongPressed(textField, Qt.Key_Backspace) : keyboardController.onKeyPressed(textField, Qt.Key_Backspace)
                    break
                case internal.kfShift:
                    internal.isShift = !internal.isShift
                    break
                case internal.kfAlt:
                    internal.isAlt = !internal.isAlt
                    internal.isNum = false
                    break
                case internal.kfNumber:
                    internal.isNum = !internal.isNum
                    internal.isAlt = false
                    break
                case internal.kfCancel:
                    root.cancel()
                    break
                case internal.kfEnter:
                    isLongPressed ? keyboardController.onKeyLongPressed(textField, Qt.Key_Return) : keyboardController.onKeyPressed(textField, Qt.Key_Return)
                    break
                default:
                    break
            }
        }

        function keyReleased(func, txt) {
            if (func === undefined) {
                func = internal.kfDefault
            }
            switch(func) {
                case internal.kfDefault:
                    keyboardController.onKeyReleased(textField, txt)
                    break
                case internal.kfBackspace:
                    keyboardController.onKeyReleased(textField, Qt.Key_Backspace)
                    break
                default:
                    break
            }
        }
    }

    // do not let pass any events to any component below the keyboard
    MouseArea {
        id: clickBlocker
        anchors.fill: parent
    }

    Rectangle {
        id: titleRect
        anchors.left: parent.left
        anchors.right: parent.right
        height: 80
        color: "steelblue"
        border.width: 1
        border.color: "#000000"
        Text {
            id: titleText
            anchors.fill: parent
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.WordWrap
            font.pointSize: 10
        }
    }

    TextField {
        id: textField
        anchors.top: titleRect.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        focus: true
        height: 80
        placeholderText: "Enter value..."
        verticalAlignment: TextInput.AlignVCenter
        background: Rectangle {
            anchors.fill: parent
            color: "#ffffff"
            border.width: 1
            border.color: "#050505"
        }
        onEditingFinished: root.confirmed(textField.text)
    }

    Item {
        id: keyboard
        anchors.top: textField.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 3
        GridLayout {
            width: parent.width
            height: parent.height
            
            columnSpacing: 3
            rowSpacing: 3
            columns: 7
            rows: 5
            Repeater {
                model: internal.keys
                delegate: Repeater {
                    model: modelData
                    property int rowIndex: index
                    delegate: MouseArea {
                        id: btn
                        Layout.columnSpan: modelData.span ?? 1
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        onPressed: internal.keyPressed(modelData.func, txt.text, false)
                        onPressAndHold: internal.keyPressed(modelData.func, txt.text, true)
                        onReleased: internal.keyReleased(modelData.func, txt.text)
                        Rectangle {
                            color: {
                                if(btn.pressed)
                                    return "white"
                                switch(modelData.func) {
                                    case internal.kfShift:
                                        return internal.isShift ? "green" : "#003554"
                                    case internal.kfAlt:
                                        return internal.isAlt ? "green" : "#003554"
                                    case internal.kfNumber:
                                        return internal.isNum ? "green" : "#003554"
                                    default:
                                        return "#003554"
                                }
                            }
                            anchors.fill: parent
                            radius: 10
                            Text {
                                id: txt
                                anchors.centerIn: parent
                                verticalAlignment: Text.AlignVCenter
                                horizontalAlignment: Text.AlignHCenter
                                text: {
                                    var val 
                                    if(internal.isNum)
                                        val = (modelData.num ?? modelData.txt ?? "")
                                    else if(internal.isAlt)
                                        val = (modelData.alt ?? modelData.txt ?? "")
                                    else 
                                        val = modelData.txt ?? ""
                                    if(internal.isShift)
                                        val = val.toUpperCase()
                                    return val
                                }
                                color: "white"
                            }
                        }
                    }
                }
            }
        }
    }
    

}