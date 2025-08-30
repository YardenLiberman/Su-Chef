import QtQuick 6.3
import QtQuick.Controls 6.3

ApplicationWindow {
    visible: true
    width: 1200
    height: 800
    title: "Su-Chef - AI Cooking Assistant"
    
    color: "#1a1a1a"
    
    Rectangle {
        anchors.fill: parent
        color: "#1a1a1a"
        
        Column {
            anchors.centerIn: parent
            spacing: 30
            
            Text {
                text: "🍳 Su-Chef Desktop"
                color: "#ffffff"
                font.pixelSize: 32
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Text {
                text: "AI-Powered Cooking Assistant"
                color: "#00ff99"
                font.pixelSize: 18
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Button {
                text: "Get Started"
                anchors.horizontalCenter: parent.horizontalCenter
                width: 200
                height: 50
                
                background: Rectangle {
                    color: parent.pressed ? "#00cc77" : "#00ff99"
                    radius: 25
                }
                
                contentItem: Text {
                    text: parent.text
                    color: "#000000"
                    font.pixelSize: 16
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                onClicked: {
                    console.log("Su-Chef Desktop App Started!")
                }
            }
        }
    }
}