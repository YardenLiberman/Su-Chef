import QtQuick 6.3
import QtQuick.Controls 6.3
import QtQuick.Layouts 6.3

ApplicationWindow {
    id: window
    visible: true
    width: 1200
    height: 800
    title: "Su-Chef - AI Cooking Assistant"
    
    color: "#1a1a1a"
    
    property bool userLoggedIn: false
    property string currentUser: ""
    property bool isCooking: false
    
    // Login dialog
    Dialog {
        id: loginDialog
        title: "Welcome to Su-Chef"
        modal: true
        anchors.centerIn: parent
        width: 400
        height: 250
        
        Rectangle {
            anchors.fill: parent
            color: "#2d2d2d"
            radius: 15
            border.color: "#00ff99"
            border.width: 2
            
            Column {
                anchors.centerIn: parent
                spacing: 20
                
                Text {
                    text: "🍳 Welcome to Su-Chef"
                    color: "#ffffff"
                    font.pixelSize: 20
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                
                Text {
                    text: "Enter your username to get started"
                    color: "#cccccc"
                    font.pixelSize: 14
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                
                Rectangle {
                    width: 300
                    height: 40
                    color: "#404040"
                    radius: 8
                    border.color: usernameField.activeFocus ? "#00ff99" : "#666666"
                    border.width: 1
                    
                    TextInput {
                        id: usernameField
                        anchors.fill: parent
                        anchors.margins: 10
                        color: "#ffffff"
                        font.pixelSize: 14
                        verticalAlignment: TextInput.AlignVCenter
                        
                        Text {
                            text: "Username"
                            color: "#888888"
                            font.pixelSize: 14
                            visible: parent.text === ""
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        
                        Keys.onReturnPressed: loginMouseArea.clicked()
                    }
                }
                
                Rectangle {
                    width: 300
                    height: 40
                    color: loginMouseArea.pressed ? "#00cc77" : "#00ff99"
                    radius: 20
                    anchors.horizontalCenter: parent.horizontalCenter
                    
                    Text {
                        id: loginButton
                        text: "Login"
                        color: "#000000"
                        font.pixelSize: 14
                        font.bold: true
                        anchors.centerIn: parent
                    }
                    
                    MouseArea {
                        id: loginMouseArea
                        anchors.fill: parent
                        onClicked: {
                            if (usernameField.text.trim() !== "") {
                                currentUser = usernameField.text.trim()
                                userLoggedIn = true
                                loginDialog.close()
                                stackView.replace(recipeFormComponent)
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Main content
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "#2d2d2d"
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                
                // Logo and title
                Row {
                    spacing: 15
                    
                    Rectangle {
                        width: 50
                        height: 50
                        radius: 25
                        color: "#00ff99"
                        
                        Text {
                            anchors.centerIn: parent
                            text: "🍳"
                            font.pixelSize: 24
                        }
                    }
                    
                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        
                        Text {
                            text: "Su-Chef"
                            color: "#ffffff"
                            font.pixelSize: 24
                            font.bold: true
                        }
                        
                        Text {
                            text: userLoggedIn ? "Welcome, " + currentUser : "AI Cooking Assistant"
                            color: "#cccccc"
                            font.pixelSize: 12
                        }
                    }
                }
                
                Item { Layout.fillWidth: true }
                
                // Status indicator
                Rectangle {
                    width: statusText.width + 20
                    height: 30
                    radius: 15
                    color: isCooking ? "#ff6b35" : "#00ff99"
                    
                    Text {
                        id: statusText
                        anchors.centerIn: parent
                        text: isCooking ? "🎤 Cooking Active" : "✅ Ready"
                        color: "#000000"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
            }
        }
        
        // Main content area
        StackView {
            id: stackView
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            initialItem: userLoggedIn ? recipeFormComponent : welcomeComponent
            
            // Welcome screen
            Component {
                id: welcomeComponent
                
                Rectangle {
                    color: "#1a1a1a"
                    
                    Column {
                        anchors.centerIn: parent
                        spacing: 30
                        
                        Text {
                            text: "🍳 Su-Chef Desktop"
                            color: "#ffffff"
                            font.pixelSize: 36
                            font.bold: true
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        
                        Text {
                            text: "Your AI-powered cooking assistant with voice guidance"
                            color: "#cccccc"
                            font.pixelSize: 18
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                        
                        Column {
                            spacing: 15
                            anchors.horizontalCenter: parent.horizontalCenter
                            
                            Text {
                                text: "✨ AI Recipe Generation"
                                color: "#00ff99"
                                font.pixelSize: 16
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                            
                            Text {
                                text: "🎤 Voice-Guided Cooking"
                                color: "#00ff99"
                                font.pixelSize: 16
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                            
                            Text {
                                text: "📚 Recipe Management"
                                color: "#00ff99"
                                font.pixelSize: 16
                                anchors.horizontalCenter: parent.horizontalCenter
                            }
                        }
                        
                        Rectangle {
                            width: 200
                            height: 50
                            color: getStartedMouseArea.pressed ? "#00cc77" : "#00ff99"
                            radius: 25
                            anchors.horizontalCenter: parent.horizontalCenter
                            
                            Text {
                                text: "Get Started"
                                color: "#000000"
                                font.pixelSize: 16
                                font.bold: true
                                anchors.centerIn: parent
                            }
                            
                            MouseArea {
                                id: getStartedMouseArea
                                anchors.fill: parent
                                onClicked: loginDialog.open()
                            }
                        }
                    }
                }
            }
            
            // Recipe form component
            Component {
                id: recipeFormComponent
                RecipeForm {}
            }
            
            // Cooking view component
            Component {
                id: cookingViewComponent
                CookingView {}
            }
            
            // History view component
            Component {
                id: historyViewComponent
                HistoryView {}
            }
        }
        
        // Bottom navigation
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            color: "#2d2d2d"
            visible: userLoggedIn
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 40
                
                Rectangle {
                    width: 120
                    height: 50
                    color: stackView.currentItem && stackView.currentItem.toString().indexOf("RecipeForm") >= 0 ? "#00ff99" : (recipeMouseArea.containsMouse ? "#404040" : "transparent")
                    radius: 10
                    border.color: stackView.currentItem && stackView.currentItem.toString().indexOf("RecipeForm") >= 0 ? "transparent" : "#666666"
                    border.width: 1
                    
                    Text {
                        text: "🍽️ Recipe"
                        color: stackView.currentItem && stackView.currentItem.toString().indexOf("RecipeForm") >= 0 ? "#000000" : "#ffffff"
                        font.pixelSize: 12
                        font.bold: stackView.currentItem && stackView.currentItem.toString().indexOf("RecipeForm") >= 0
                        anchors.centerIn: parent
                    }
                    
                    MouseArea {
                        id: recipeMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: stackView.replace(recipeFormComponent)
                    }
                }
                
                Rectangle {
                    width: 120
                    height: 50
                    color: stackView.currentItem && stackView.currentItem.toString().indexOf("CookingView") >= 0 ? "#00ff99" : (cookingMouseArea.containsMouse ? "#404040" : "transparent")
                    radius: 10
                    border.color: stackView.currentItem && stackView.currentItem.toString().indexOf("CookingView") >= 0 ? "transparent" : "#666666"
                    border.width: 1
                    opacity: isCooking ? 1.0 : 0.5
                    
                    Text {
                        text: "👨‍🍳 Cooking"
                        color: stackView.currentItem && stackView.currentItem.toString().indexOf("CookingView") >= 0 ? "#000000" : "#ffffff"
                        font.pixelSize: 12
                        font.bold: stackView.currentItem && stackView.currentItem.toString().indexOf("CookingView") >= 0
                        anchors.centerIn: parent
                    }
                    
                    MouseArea {
                        id: cookingMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: isCooking
                        onClicked: stackView.replace(cookingViewComponent)
                    }
                }
                
                Rectangle {
                    width: 120
                    height: 50
                    color: stackView.currentItem && stackView.currentItem.toString().indexOf("HistoryView") >= 0 ? "#00ff99" : (historyMouseArea.containsMouse ? "#404040" : "transparent")
                    radius: 10
                    border.color: stackView.currentItem && stackView.currentItem.toString().indexOf("HistoryView") >= 0 ? "transparent" : "#666666"
                    border.width: 1
                    
                    Text {
                        text: "📚 History"
                        color: stackView.currentItem && stackView.currentItem.toString().indexOf("HistoryView") >= 0 ? "#000000" : "#ffffff"
                        font.pixelSize: 12
                        font.bold: stackView.currentItem && stackView.currentItem.toString().indexOf("HistoryView") >= 0
                        anchors.centerIn: parent
                    }
                    
                    MouseArea {
                        id: historyMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: stackView.replace(historyViewComponent)
                    }
                }
            }
        }
    }
    
    // Status bar
    Rectangle {
        id: statusBar
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 30
        color: "#404040"
        visible: statusMessage.text !== ""
        
        Text {
            id: statusMessage
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: 10
            color: "#ffffff"
            font.pixelSize: 12
        }
        
        Timer {
            id: statusTimer
            interval: 5000
            onTriggered: statusMessage.text = ""
        }
    }
    
    // Show login dialog on startup
    Component.onCompleted: {
        if (!userLoggedIn) {
            loginDialog.open()
        }
    }
    
    function showStatus(message) {
        statusMessage.text = message
        statusTimer.restart()
    }
}