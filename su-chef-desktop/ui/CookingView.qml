import QtQuick 6.3
import QtQuick.Controls 6.3
import QtQuick.Layouts 6.3

Rectangle {
    id: root
    color: "#1a1a1a"
    
    property int currentStep: 0
    property var recipeSteps: []  // Will be populated from backend
    property string heardText: ""
    property bool isListening: false
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 30
        
        // Title
        Text {
            text: "👨‍🍳 Voice-Guided Cooking"
            color: "#ffffff"
            font.pixelSize: 28
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
        }
        
        // Voice status indicator
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            width: 350
            height: 100
            color: "#2d2d2d"
            radius: 15
            border.color: isListening ? "#ff6b35" : "#00ff99"
            border.width: 2
            
            Column {
                anchors.centerIn: parent
                spacing: 10
                
                Text {
                    text: isListening ? "🎤 Listening..." : "🔊 Speaking"
                    color: isListening ? "#ff6b35" : "#00ff99"
                    font.pixelSize: 18
                    font.bold: true
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                
                Text {
                    text: heardText || "Say 'next', 'repeat', 'back', or ask questions"
                    color: "#cccccc"
                    font.pixelSize: 14
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: 320
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            
            // Animated listening indicator
            Rectangle {
                anchors.centerIn: parent
                width: 80
                height: 80
                radius: 40
                color: "transparent"
                border.color: isListening ? "#ff6b35" : "transparent"
                border.width: 3
                visible: isListening
                
                SequentialAnimation on scale {
                    running: isListening
                    loops: Animation.Infinite
                    NumberAnimation { from: 1.0; to: 1.3; duration: 1000 }
                    NumberAnimation { from: 1.3; to: 1.0; duration: 1000 }
                }
                
                SequentialAnimation on opacity {
                    running: isListening
                    loops: Animation.Infinite
                    NumberAnimation { from: 0.3; to: 1.0; duration: 1000 }
                    NumberAnimation { from: 1.0; to: 0.3; duration: 1000 }
                }
            }
        }
        
        // Current step display
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 150
            color: "#2d2d2d"
            radius: 15
            border.color: "#00ff99"
            border.width: 1
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                
                Text {
                    text: `Step ${currentStep + 1} of ${recipeSteps.length}`
                    color: "#00ff99"
                    font.pixelSize: 16
                    font.bold: true
                }
                
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    Text {
                        text: currentStep < recipeSteps.length ? recipeSteps[currentStep] : "Recipe completed!"
                        color: "#ffffff"
                        font.pixelSize: 20
                        wrapMode: Text.WordWrap
                        width: parent.parent.width - 40
                    }
                }
            }
        }
        
        // Step navigation
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 250
            color: "#2d2d2d"
            radius: 15
            border.color: "#666666"
            border.width: 1
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                
                Text {
                    text: "📝 All Steps"
                    color: "#ffffff"
                    font.pixelSize: 18
                    font.bold: true
                }
                
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    Column {
                        width: parent.width
                        spacing: 8
                        
                        Repeater {
                            model: recipeSteps
                            
                            Rectangle {
                                width: parent.width
                                height: stepText.height + 20
                                color: index === currentStep ? "#00ff9930" : "transparent"
                                radius: 8
                                border.color: index === currentStep ? "#00ff99" : "transparent"
                                border.width: 1
                                
                                Row {
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.margins: 10
                                    spacing: 15
                                    
                                    Rectangle {
                                        width: 30
                                        height: 30
                                        radius: 15
                                        color: index === currentStep ? "#00ff99" : "#666666"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: index + 1
                                            color: index === currentStep ? "#000000" : "#ffffff"
                                            font.pixelSize: 14
                                            font.bold: true
                                        }
                                    }
                                    
                                    Text {
                                        id: stepText
                                        text: modelData
                                        color: index === currentStep ? "#ffffff" : "#cccccc"
                                        font.pixelSize: 14
                                        font.bold: index === currentStep
                                        wrapMode: Text.WordWrap
                                        width: parent.parent.width - 80
                                    }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        currentStep = index
                                        simulateVoiceResponse()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Control buttons
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "#2d2d2d"
            radius: 15
            border.color: "#666666"
            border.width: 1
            
            RowLayout {
                anchors.centerIn: parent
                spacing: 20
                
                Rectangle {
                    width: 100
                    height: 50
                    color: backMouseArea.pressed ? "#0066cc" : (currentStep > 0 ? "#0088ff" : "#666666")
                    radius: 10
                    
                    Text {
                        text: "⬅️ Back"
                        color: currentStep > 0 ? "#ffffff" : "#cccccc"
                        font.pixelSize: 14
                        font.bold: true
                        anchors.centerIn: parent
                    }
                    
                                            MouseArea {
                            id: backMouseArea
                            anchors.fill: parent
                            enabled: currentStep > 0
                            onClicked: {
                                backend.backStep()
                            }
                        }
                }
                
                Rectangle {
                    width: 100
                    height: 50
                    color: repeatMouseArea.pressed ? "#cc8800" : "#ffaa00"
                    radius: 10
                    
                    Text {
                        text: "🔄 Repeat"
                        color: "#000000"
                        font.pixelSize: 14
                        font.bold: true
                        anchors.centerIn: parent
                    }
                    
                                            MouseArea {
                            id: repeatMouseArea
                            anchors.fill: parent
                            onClicked: backend.repeatStep()
                        }
                }
                
                Rectangle {
                    width: 100
                    height: 50
                    color: nextMouseArea.pressed ? "#00cc77" : (currentStep < recipeSteps.length - 1 ? "#00ff99" : "#666666")
                    radius: 10
                    
                    Text {
                        text: "➡️ Next"
                        color: currentStep < recipeSteps.length - 1 ? "#000000" : "#cccccc"
                        font.pixelSize: 14
                        font.bold: true
                        anchors.centerIn: parent
                    }
                    
                                            MouseArea {
                            id: nextMouseArea
                            anchors.fill: parent
                            enabled: currentStep < recipeSteps.length - 1
                            onClicked: {
                                backend.nextStep()
                            }
                        }
                }
                
                Rectangle {
                    width: 100
                    height: 50
                    color: stopMouseArea.pressed ? "#cc3333" : "#ff4444"
                    radius: 10
                    
                    Text {
                        text: "⏹️ Stop"
                        color: "#ffffff"
                        font.pixelSize: 14
                        font.bold: true
                        anchors.centerIn: parent
                    }
                    
                                            MouseArea {
                            id: stopMouseArea
                            anchors.fill: parent
                            onClicked: {
                                backend.stopCooking()
                            }
                        }
                }
            }
        }
        
        // Voice commands help
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 140
            color: "#2d2d2d"
            radius: 15
            border.color: "#666666"
            border.width: 1
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15
                
                Text {
                    text: "🎤 Voice Commands"
                    color: "#ffffff"
                    font.pixelSize: 16
                    font.bold: true
                }
                
                GridLayout {
                    columns: 2
                    columnSpacing: 30
                    rowSpacing: 8
                    
                    Text {
                        text: "• \"Next\" - Go to next step"
                        color: "#cccccc"
                        font.pixelSize: 12
                    }
                    
                    Text {
                        text: "• \"Repeat\" - Repeat current step"
                        color: "#cccccc"
                        font.pixelSize: 12
                    }
                    
                    Text {
                        text: "• \"Back\" - Go to previous step"
                        color: "#cccccc"
                        font.pixelSize: 12
                    }
                    
                    Text {
                        text: "• \"Ingredients\" - List ingredients"
                        color: "#cccccc"
                        font.pixelSize: 12
                    }
                    
                    Text {
                        text: "• \"Help\" - Get cooking tips"
                        color: "#cccccc"
                        font.pixelSize: 12
                    }
                    
                    Text {
                        text: "• \"Stop\" - End cooking session"
                        color: "#cccccc"
                        font.pixelSize: 12
                    }
                }
                
                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 200
                    height: 35
                    color: listenMouseArea.pressed ? "#cc5500" : "#ff6b35"
                    radius: 17
                    
                    Text {
                        text: isListening ? "🔇 Stop Listening" : "🎤 Start Listening"
                        color: "#ffffff"
                        font.pixelSize: 12
                        font.bold: true
                        anchors.centerIn: parent
                    }
                    
                    MouseArea {
                        id: listenMouseArea
                        anchors.fill: parent
                        onClicked: {
                            isListening = !isListening
                            if (isListening) {
                                // Start real voice recognition (same as mini app)
                                backend.startListening()
                            } else {
                                backend.stopListening()
                            }
                        }
                    }
                }
                
                // Test microphone button (same as mini app)
                Rectangle {
                    width: 200
                    height: 50
                    color: testMicMouseArea.containsMouse ? "#404040" : "#333333"
                    radius: 10
                    border.color: "#666666"
                    border.width: 1
                    
                    Text {
                        text: "🎙️ Test Microphone"
                        color: "#ffffff"
                        font.pixelSize: 14
                        font.bold: true
                        anchors.centerIn: parent
                    }
                    
                    MouseArea {
                        id: testMicMouseArea
                        anchors.fill: parent
                        onClicked: {
                            backend.testMicrophone()
                        }
                    }
                }
            }
        }
    }
    
    // Functions
    function simulateVoiceResponse() {
        window.showStatus(`Speaking step ${currentStep + 1}...`)
        
        // Simulate TTS speaking
        var timer = Qt.createQmlObject("import QtQuick 6.3; Timer {}", root)
        timer.interval = 1000
        timer.triggered.connect(function() {
            window.showStatus("Ready for voice commands")
            timer.destroy()
        })
        timer.start()
    }
    
    function simulateListening() {
        if (!isListening) return
        
        heardText = "Listening for commands..."
        
        var timer = Qt.createQmlObject("import QtQuick 6.3; Timer {}", root)
        timer.interval = 3000
        timer.triggered.connect(function() {
            var commands = ["next", "repeat", "back", "what ingredients do I need?", "help with this step"]
            var randomCommand = commands[Math.floor(Math.random() * commands.length)]
            heardText = `"${randomCommand}"`
            
            // Process the command
            if (randomCommand === "next" && currentStep < recipeSteps.length - 1) {
                currentStep++
            } else if (randomCommand === "back" && currentStep > 0) {
                currentStep--
            }
            
            isListening = false
            window.showStatus(`Heard: "${randomCommand}"`)
            
            // Clear heard text after a delay
            var clearTimer = Qt.createQmlObject("import QtQuick 6.3; Timer {}", root)
            clearTimer.interval = 3000
            clearTimer.triggered.connect(function() {
                heardText = ""
                clearTimer.destroy()
            })
            clearTimer.start()
            
            timer.destroy()
        })
        timer.start()
    }
    
    // Backend connections
    Connections {
        target: backend
        
        function onStepChanged(step) {
            currentStep = step
        }
        
        function onHeardText(text) {
            heardText = text
            // Clear heard text after a delay
            var clearTimer = Qt.createQmlObject("import QtQuick 6.3; Timer {}", root)
            clearTimer.interval = 3000
            clearTimer.triggered.connect(function() {
                heardText = ""
                clearTimer.destroy()
            })
            clearTimer.start()
        }
        
        function onStatusChanged(status) {
            // Update listening state based on status
            isListening = status.includes("Listening") || status.includes("listening")
        }
        
        function onCookingStopped() {
            window.isCooking = false
            stackView.replace(recipeFormComponent)
        }
    }
    
    // Connect to backend signals
    Connections {
        target: backend
        
        function onRecipeStepsChanged(steps) {
            console.log("Received recipe steps:", steps)
            recipeSteps = steps
            currentStep = 0  // Start at first step
        }
        
        function onStepChanged(stepIndex) {
            console.log("Step changed to:", stepIndex)
            currentStep = stepIndex
        }
        
        function onStatusChanged(status) {
            console.log("Status:", status)
        }
        
        function onHeardText(text) {
            heardText = text
            console.log("Heard:", text)
        }
    }
    
    Component.onCompleted: {
        console.log("CookingView loaded")
        // Don't auto-start cooking - let RecipeForm handle it
    }
}