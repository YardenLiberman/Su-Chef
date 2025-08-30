import QtQuick 6.3
import QtQuick.Controls 6.3
import QtQuick.Layouts 6.3

Rectangle {
    id: root
    color: "#1a1a1a"
    
    property var currentRecipe: null
    property bool isGenerating: false
    
    ScrollView {
        anchors.fill: parent
        anchors.margins: 20
        
        ColumnLayout {
            width: parent.width
            spacing: 30
            
            // Title
            Text {
                text: "🍽️ Create New Recipe"
                color: "#ffffff"
                font.pixelSize: 28
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }
            
            // Recipe preferences form
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: formColumn.height + 40
                color: "#2d2d2d"
                radius: 15
                border.color: "#00ff99"
                border.width: 1
                
                ColumnLayout {
                    id: formColumn
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 25
                    
                    // Meal type
                    Column {
                        spacing: 10
                        
                        Text {
                            text: "Meal Type"
                            color: "#ffffff"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Row {
                            spacing: 20
                            
                            RadioButton {
                                id: breakfastRadio
                                text: "🌅 Breakfast"
                                checked: true
                                
                                Rectangle {
                                    width: 16
                                    height: 16
                                    radius: 8
                                    border.color: "#00ff99"
                                    border.width: 1
                                    color: parent.checked ? "#00ff99" : "transparent"
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                
                                Text {
                                    text: parent.text
                                    color: "#ffffff"
                                    font.pixelSize: 14
                                    anchors.left: parent.left
                                    anchors.leftMargin: 25
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                            
                            RadioButton {
                                id: lunchRadio
                                text: "🌞 Lunch"
                                
                                Rectangle {
                                    width: 16
                                    height: 16
                                    radius: 8
                                    border.color: "#00ff99"
                                    border.width: 1
                                    color: parent.checked ? "#00ff99" : "transparent"
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                
                                Text {
                                    text: parent.text
                                    color: "#ffffff"
                                    font.pixelSize: 14
                                    anchors.left: parent.left
                                    anchors.leftMargin: 25
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                            
                            RadioButton {
                                id: dinnerRadio
                                text: "🌙 Dinner"
                                
                                Rectangle {
                                    width: 16
                                    height: 16
                                    radius: 8
                                    border.color: "#00ff99"
                                    border.width: 1
                                    color: parent.checked ? "#00ff99" : "transparent"
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                
                                Text {
                                    text: parent.text
                                    color: "#ffffff"
                                    font.pixelSize: 14
                                    anchors.left: parent.left
                                    anchors.leftMargin: 25
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                            
                            RadioButton {
                                id: snackRadio
                                text: "🍿 Snack"
                                
                                Rectangle {
                                    width: 16
                                    height: 16
                                    radius: 8
                                    border.color: "#00ff99"
                                    border.width: 1
                                    color: parent.checked ? "#00ff99" : "transparent"
                                    anchors.left: parent.left
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                
                                Text {
                                    text: parent.text
                                    color: "#ffffff"
                                    font.pixelSize: 14
                                    anchors.left: parent.left
                                    anchors.leftMargin: 25
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                        }
                    }
                    
                    // Cooking time
                    Column {
                        spacing: 10
                        
                        Text {
                            text: "Maximum Cooking Time"
                            color: "#ffffff"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Row {
                            spacing: 15
                            
                            Rectangle {
                                width: 300
                                height: 6
                                color: "#666666"
                                radius: 3
                                
                                Rectangle {
                                    width: parent.width * (timeSlider.value - timeSlider.from) / (timeSlider.to - timeSlider.from)
                                    height: parent.height
                                    color: "#00ff99"
                                    radius: 3
                                }
                                
                                Rectangle {
                                    id: timeHandle
                                    width: 20
                                    height: 20
                                    radius: 10
                                    color: "#00ff99"
                                    border.color: "#ffffff"
                                    border.width: 1
                                    x: (parent.width - width) * (timeSlider.value - timeSlider.from) / (timeSlider.to - timeSlider.from)
                                    y: -7
                                }
                                
                                MouseArea {
                                    id: timeSlider
                                    anchors.fill: parent
                                    
                                    property real from: 5
                                    property real to: 120
                                    property real value: 30
                                    
                                    onPressed: {
                                        value = Math.max(from, Math.min(to, from + (mouseX / width) * (to - from)))
                                    }
                                    
                                    onPositionChanged: {
                                        if (pressed) {
                                            value = Math.max(from, Math.min(to, from + (mouseX / width) * (to - from)))
                                        }
                                    }
                                }
                            }
                            
                            Text {
                                text: Math.round(timeSlider.value) + " min"
                                color: "#00ff99"
                                font.pixelSize: 16
                                font.bold: true
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }
                    
                    // Skill level
                    Column {
                        spacing: 10
                        
                        Text {
                            text: "Skill Level"
                            color: "#ffffff"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Rectangle {
                            width: 200
                            height: 40
                            color: "#404040"
                            radius: 8
                            border.color: skillMouseArea.containsMouse ? "#00ff99" : "#666666"
                            border.width: 1
                            
                            Text {
                                id: skillText
                                text: "👶 Beginner"
                                color: "#ffffff"
                                font.pixelSize: 14
                                anchors.left: parent.left
                                anchors.leftMargin: 10
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            
                            Text {
                                text: "▼"
                                color: "#ffffff"
                                font.pixelSize: 12
                                anchors.right: parent.right
                                anchors.rightMargin: 10
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            
                            MouseArea {
                                id: skillMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: skillPopup.open()
                            }
                            
                            Popup {
                                id: skillPopup
                                y: parent.height
                                width: parent.width
                                height: 120
                                
                                Rectangle {
                                    anchors.fill: parent
                                    color: "#404040"
                                    radius: 8
                                    border.color: "#666666"
                                    border.width: 1
                                    
                                    Column {
                                        anchors.fill: parent
                                        
                                        Rectangle {
                                            width: parent.width
                                            height: 40
                                            color: skill1MouseArea.containsMouse ? "#555555" : "transparent"
                                            
                                            Text {
                                                text: "👶 Beginner"
                                                color: "#ffffff"
                                                font.pixelSize: 14
                                                anchors.left: parent.left
                                                anchors.leftMargin: 10
                                                anchors.verticalCenter: parent.verticalCenter
                                            }
                                            
                                            MouseArea {
                                                id: skill1MouseArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    skillText.text = "👶 Beginner"
                                                    skillPopup.close()
                                                }
                                            }
                                        }
                                        
                                        Rectangle {
                                            width: parent.width
                                            height: 40
                                            color: skill2MouseArea.containsMouse ? "#555555" : "transparent"
                                            
                                            Text {
                                                text: "👨‍🍳 Intermediate"
                                                color: "#ffffff"
                                                font.pixelSize: 14
                                                anchors.left: parent.left
                                                anchors.leftMargin: 10
                                                anchors.verticalCenter: parent.verticalCenter
                                            }
                                            
                                            MouseArea {
                                                id: skill2MouseArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    skillText.text = "👨‍🍳 Intermediate"
                                                    skillPopup.close()
                                                }
                                            }
                                        }
                                        
                                        Rectangle {
                                            width: parent.width
                                            height: 40
                                            color: skill3MouseArea.containsMouse ? "#555555" : "transparent"
                                            
                                            Text {
                                                text: "⭐ Advanced"
                                                color: "#ffffff"
                                                font.pixelSize: 14
                                                anchors.left: parent.left
                                                anchors.leftMargin: 10
                                                anchors.verticalCenter: parent.verticalCenter
                                            }
                                            
                                            MouseArea {
                                                id: skill3MouseArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    skillText.text = "⭐ Advanced"
                                                    skillPopup.close()
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // Available ingredients
                    Column {
                        spacing: 10
                        
                        Text {
                            text: "Available Ingredients (optional)"
                            color: "#ffffff"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Rectangle {
                            width: 400
                            height: 40
                            color: "#404040"
                            radius: 8
                            border.color: ingredientsField.activeFocus ? "#00ff99" : "#666666"
                            border.width: 1
                            
                            TextInput {
                                id: ingredientsField
                                anchors.fill: parent
                                anchors.margins: 10
                                color: "#ffffff"
                                font.pixelSize: 14
                                verticalAlignment: TextInput.AlignVCenter
                                
                                Text {
                                    text: "e.g., chicken, rice, tomatoes (comma-separated)"
                                    color: "#888888"
                                    font.pixelSize: 14
                                    visible: parent.text === ""
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                        }
                    }
                    
                    // Generate button - improved design
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 250
                        height: 60
                        color: generateMouseArea.pressed ? "#00cc77" : (isGenerating ? "#666666" : "#00ff99")
                        radius: 30
                        border.color: "#ffffff"
                        border.width: isGenerating ? 0 : 2
                        
                        // Subtle shadow effect
                        Rectangle {
                            anchors.fill: parent
                            anchors.topMargin: 3
                            color: "#000000"
                            opacity: 0.2
                            radius: parent.radius
                            z: -1
                        }
                        
                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 10
                            
                            Text {
                                text: isGenerating ? "🔄" : "✨"
                                font.pixelSize: 20
                            }
                            
                            Text {
                                text: isGenerating ? "Generating..." : "Generate Recipe"
                                color: isGenerating ? "#cccccc" : "#000000"
                                font.pixelSize: 18
                                font.bold: true
                            }
                        }
                        
                        MouseArea {
                            id: generateMouseArea
                            anchors.fill: parent
                            enabled: !isGenerating
                            onClicked: generateRecipe()
                        }
                    }
                }
            }
            
            // Generated recipe display
            Rectangle {
                id: recipeDisplay
                Layout.fillWidth: true
                Layout.preferredHeight: recipeContent.height + 40
                color: "#2d2d2d"
                radius: 15
                border.color: "#00ff99"
                border.width: 1
                visible: currentRecipe !== null
                
                Column {
                    id: recipeContent
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 20
                    
                    // Recipe title
                    Text {
                        text: currentRecipe ? (currentRecipe.name || "Generated Recipe") : ""
                        color: "#ffffff"
                        font.pixelSize: 24
                        font.bold: true
                    }
                    
                    // Recipe info
                    Row {
                        spacing: 30
                        
                        Text {
                            text: "⏱️ " + (currentRecipe ? (currentRecipe.cooking_time + " min") : "")
                            color: "#00ff99"
                            font.pixelSize: 14
                        }
                        
                        Text {
                            text: "👨‍🍳 " + (currentRecipe ? currentRecipe.skill_level : "")
                            color: "#00ff99"
                            font.pixelSize: 14
                        }
                        
                        Text {
                            text: "🍽️ " + (currentRecipe ? currentRecipe.meal_type : "")
                            color: "#00ff99"
                            font.pixelSize: 14
                        }
                    }
                    
                    // Ingredients
                    Column {
                        spacing: 10
                        
                        Text {
                            text: "📋 Ingredients"
                            color: "#ffffff"
                            font.pixelSize: 18
                            font.bold: true
                        }
                        
                        Column {
                            spacing: 5
                            Repeater {
                                model: currentRecipe ? currentRecipe.ingredients : []
                                
                                Text {
                                    text: "• " + modelData
                                    color: "#cccccc"
                                    font.pixelSize: 14
                                }
                            }
                        }
                    }
                    
                    // Instructions
                    Column {
                        spacing: 10
                        
                        Text {
                            text: "📝 Instructions"
                            color: "#ffffff"
                            font.pixelSize: 18
                            font.bold: true
                        }
                        
                        Column {
                            spacing: 8
                            Repeater {
                                model: currentRecipe ? currentRecipe.instructions : []
                                
                                Text {
                                    text: (index + 1) + ". " + modelData
                                    color: "#cccccc"
                                    font.pixelSize: 14
                                    wrapMode: Text.WordWrap
                                    width: recipeContent.width - 40
                                }
                            }
                        }
                    }
                    
                    // Action buttons
                    Row {
                        spacing: 20
                        anchors.horizontalCenter: parent.horizontalCenter
                        
                        Rectangle {
                            width: 150
                            height: 40
                            color: cookMouseArea.pressed ? "#cc5500" : "#ff6b35"
                            radius: 20
                            
                            Text {
                                text: "🎤 Start Cooking"
                                color: "#ffffff"
                                font.pixelSize: 14
                                font.bold: true
                                anchors.centerIn: parent
                            }
                            
                            MouseArea {
                                id: cookMouseArea
                                anchors.fill: parent
                                onClicked: {
                                    window.isCooking = true
                                    window.showStatus("Starting cooking session...")
                                    stackView.replace(cookingViewComponent)
                                }
                            }
                        }
                        
                        Rectangle {
                            width: 150
                            height: 40
                            color: saveMouseArea.pressed ? "#0066cc" : "#0088ff"
                            radius: 20
                            
                            Text {
                                text: "💾 Save Recipe"
                                color: "#ffffff"
                                font.pixelSize: 14
                                font.bold: true
                                anchors.centerIn: parent
                            }
                            
                            MouseArea {
                                id: saveMouseArea
                                anchors.fill: parent
                                onClicked: {
                                    window.showStatus("Recipe saved!")
                                }
                            }
                        }
                        
                        Rectangle {
                            width: 150
                            height: 40
                            color: newMouseArea.pressed ? "#666666" : "#888888"
                            radius: 20
                            
                            Text {
                                text: "🔄 New Recipe"
                                color: "#ffffff"
                                font.pixelSize: 14
                                font.bold: true
                                anchors.centerIn: parent
                            }
                            
                            MouseArea {
                                id: newMouseArea
                                anchors.fill: parent
                                onClicked: {
                                    currentRecipe = null
                                    isGenerating = false
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Functions
    function generateRecipe() {
        isGenerating = true
        
        // Get selected meal type
        let mealType = getMealType()
        
        // Get skill level
        let skillLevel = "beginner"
        if (skillText.text.indexOf("Intermediate") >= 0) skillLevel = "intermediate"
        else if (skillText.text.indexOf("Advanced") >= 0) skillLevel = "advanced"
        
        // Get dietary restrictions (none for now)
        let diet = "none"
        
        // Parse ingredients
        let ingredients = []
        if (ingredientsField.text.trim() !== "") {
            ingredients = ingredientsField.text.split(",").map(s => s.trim()).filter(s => s !== "")
        }
        
        // Call backend to generate real recipe (pass ingredients as string like CLI)
        backend.generateRecipe(mealType, Math.round(timeSlider.value), skillLevel, diet, ingredientsField.text)
    }
    
    // Backend connections
    Connections {
        target: backend
        
        function onRecipeGenerated(recipe) {
            currentRecipe = recipe
            isGenerating = false
            
            // Automatically start cooking session with the generated recipe
            console.log("Starting cooking session with generated recipe")
            backend.startCooking(recipe)
        }
        
        function onCookingStarted() {
            // Switch to cooking view when cooking starts
            console.log("Cooking started - switching to cooking view")
            window.isCooking = true
            stackView.replace(cookingViewComponent)
        }
        
        function onErrorOccurred(error) {
            isGenerating = false
            window.showStatus("❌ " + error)
        }
    }
    
    function getMealType() {
        if (breakfastRadio.checked) return "breakfast"
        if (lunchRadio.checked) return "lunch"
        if (dinnerRadio.checked) return "dinner"
        if (snackRadio.checked) return "snack"
        return "dinner"
    }
}