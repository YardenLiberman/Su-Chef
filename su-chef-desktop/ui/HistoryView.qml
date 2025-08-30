import QtQuick 6.3
import QtQuick.Controls 6.3
import QtQuick.Layouts 6.3

Rectangle {
    id: root
    color: "#1a1a1a"
    
    property var recipes: [
        {
            id: 1,
            name: "Pasta Carbonara",
            meal_type: "dinner",
            cooking_time: 25,
            skill_level: "intermediate",
            cooked: true,
            liked: true,
            ingredients: ["400g spaghetti", "200g pancetta", "4 eggs", "100g cheese"],
            instructions: ["Boil water", "Cook pasta", "Prepare sauce", "Combine and serve"]
        },
        {
            id: 2,
            name: "Chicken Stir Fry",
            meal_type: "lunch",
            cooking_time: 20,
            skill_level: "beginner",
            cooked: true,
            liked: false,
            ingredients: ["300g chicken", "Mixed vegetables", "Soy sauce", "Rice"],
            instructions: ["Cut chicken", "Heat oil", "Stir fry", "Serve with rice"]
        },
        {
            id: 3,
            name: "Chocolate Pancakes",
            meal_type: "breakfast",
            cooking_time: 15,
            skill_level: "beginner",
            cooked: false,
            liked: false,
            ingredients: ["2 cups flour", "2 eggs", "Milk", "Cocoa powder"],
            instructions: ["Mix dry ingredients", "Add wet ingredients", "Cook pancakes", "Serve hot"]
        }
    ]
    property var selectedRecipe: null
    property string currentFilter: "all"
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20
        
        // Left panel - Recipe list
        Rectangle {
            Layout.preferredWidth: 400
            Layout.fillHeight: true
            color: "#2d2d2d"
            radius: 15
            border.color: "#00ff99"
            border.width: 1
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20
                
                // Title and refresh
                Row {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    Text {
                        text: "📚 Recipe History"
                        color: "#ffffff"
                        font.pixelSize: 22
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    Rectangle {
                        width: 40
                        height: 40
                        color: refreshMouseArea.pressed ? "#00cc77" : "#00ff99"
                        radius: 20
                        
                        Text {
                            text: "🔄"
                            color: "#000000"
                            font.pixelSize: 16
                            anchors.centerIn: parent
                        }
                        
                        MouseArea {
                            id: refreshMouseArea
                            anchors.fill: parent
                            onClicked: {
                                window.showStatus("Recipes refreshed")
                            }
                        }
                    }
                }
                
                // Filter buttons
                Row {
                    spacing: 10
                    
                    Rectangle {
                        width: 60
                        height: 35
                        color: currentFilter === "all" ? "#00ff99" : (allMouseArea.containsMouse ? "#404040" : "transparent")
                        radius: 17
                        border.color: "#666666"
                        border.width: 1
                        
                        Text {
                            text: "All"
                            color: currentFilter === "all" ? "#000000" : "#ffffff"
                            font.pixelSize: 12
                            font.bold: currentFilter === "all"
                            anchors.centerIn: parent
                        }
                        
                        MouseArea {
                            id: allMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: currentFilter = "all"
                        }
                    }
                    
                    Rectangle {
                        width: 80
                        height: 35
                        color: currentFilter === "cooked" ? "#00ff99" : (cookedMouseArea.containsMouse ? "#404040" : "transparent")
                        radius: 17
                        border.color: "#666666"
                        border.width: 1
                        
                        Text {
                            text: "Cooked"
                            color: currentFilter === "cooked" ? "#000000" : "#ffffff"
                            font.pixelSize: 12
                            font.bold: currentFilter === "cooked"
                            anchors.centerIn: parent
                        }
                        
                        MouseArea {
                            id: cookedMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: currentFilter = "cooked"
                        }
                    }
                    
                    Rectangle {
                        width: 120
                        height: 35
                        color: currentFilter === "liked" ? "#00ff99" : (likedMouseArea.containsMouse ? "#404040" : "transparent")
                        radius: 17
                        border.color: "#666666"
                        border.width: 1
                        
                        Text {
                            text: "⭐ Favorites"
                            color: currentFilter === "liked" ? "#000000" : "#ffffff"
                            font.pixelSize: 12
                            font.bold: currentFilter === "liked"
                            anchors.centerIn: parent
                        }
                        
                        MouseArea {
                            id: likedMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: currentFilter = "liked"
                        }
                    }
                }
                
                // Recipe list
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    
                    Column {
                        width: parent.width
                        spacing: 10
                        
                        Repeater {
                            model: getFilteredRecipes()
                            
                            Rectangle {
                                width: parent.width
                                height: 120  // Increased height to prevent overlap
                                color: recipeMouseArea.containsMouse ? "#404040" : "#333333"
                                radius: 10
                                border.color: selectedRecipe && selectedRecipe.id === modelData.id ? "#00ff99" : "transparent"
                                border.width: 2
                                
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20  // More margin
                                    spacing: 20  // More spacing
                                    
                                    // Recipe icon
                                    Rectangle {
                                        width: 60
                                        height: 60
                                        radius: 30
                                        color: "#00ff99"
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: getRecipeIcon(modelData.meal_type)
                                            font.pixelSize: 24
                                        }
                                    }
                                    
                                    // Recipe info
                                    Column {
                                        Layout.fillWidth: true
                                        spacing: 8  // More spacing between text elements
                                        
                                        Text {
                                            text: modelData.name
                                            color: "#ffffff"
                                            font.pixelSize: 16
                                            font.bold: true
                                            elide: Text.ElideRight
                                            width: parent.width
                                        }
                                        
                                        Row {
                                            spacing: 15
                                            
                                            Text {
                                                text: "⏱️ " + modelData.cooking_time + " min"
                                                color: "#cccccc"
                                                font.pixelSize: 12
                                            }
                                            
                                            Text {
                                                text: "👨‍🍳 " + modelData.skill_level
                                                color: "#cccccc"
                                                font.pixelSize: 12
                                            }
                                        }
                                        
                                        Text {
                                            text: "🍽️ " + modelData.meal_type
                                            color: "#cccccc"
                                            font.pixelSize: 12
                                        }
                                    }
                                    
                                    // Status indicators
                                    Column {
                                        spacing: 5
                                        
                                        Text {
                                            text: modelData.cooked ? "✅" : ""
                                            font.pixelSize: 18
                                            visible: modelData.cooked
                                        }
                                        
                                        Text {
                                            text: modelData.liked ? "⭐" : ""
                                            font.pixelSize: 18
                                            visible: modelData.liked
                                        }
                                    }
                                }
                                
                                MouseArea {
                                    id: recipeMouseArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    
                                    onClicked: {
                                        selectedRecipe = modelData
                                        window.showStatus("Selected: " + modelData.name)
                                    }
                                }
                            }
                        }
                        
                        // Empty state
                        Rectangle {
                            width: parent.width
                            height: 200
                            color: "transparent"
                            visible: getFilteredRecipes().length === 0
                            
                            Column {
                                anchors.centerIn: parent
                                spacing: 15
                                
                                Text {
                                    text: "📭"
                                    color: "#666666"
                                    font.pixelSize: 48
                                    anchors.horizontalCenter: parent.horizontalCenter
                                }
                                
                                Text {
                                    text: "No recipes found"
                                    color: "#666666"
                                    font.pixelSize: 18
                                    font.bold: true
                                    anchors.horizontalCenter: parent.horizontalCenter
                                }
                                
                                Text {
                                    text: "Try generating some recipes first!"
                                    color: "#888888"
                                    font.pixelSize: 14
                                    anchors.horizontalCenter: parent.horizontalCenter
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // Right panel - Recipe details
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#2d2d2d"
            radius: 15
            border.color: "#666666"
            border.width: 1
            
            ScrollView {
                anchors.fill: parent
                anchors.margins: 20
                
                ColumnLayout {
                    width: parent.width
                    spacing: 25
                    
                    // Recipe details header
                    Text {
                        text: selectedRecipe ? selectedRecipe.name : "Select a recipe to view details"
                        color: "#ffffff"
                        font.pixelSize: 26
                        font.bold: true
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    // Recipe info (only show if recipe selected)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: infoColumn.height + 30
                        color: "#404040"
                        radius: 12
                        visible: selectedRecipe !== null
                        
                        Column {
                            id: infoColumn
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 15
                            
                            Row {
                                spacing: 40
                                
                                Text {
                                    text: "🍽️ " + (selectedRecipe ? selectedRecipe.meal_type : "")
                                    color: "#00ff99"
                                    font.pixelSize: 16
                                    font.bold: true
                                }
                                
                                Text {
                                    text: "⏱️ " + (selectedRecipe ? selectedRecipe.cooking_time : "") + " minutes"
                                    color: "#00ff99"
                                    font.pixelSize: 16
                                    font.bold: true
                                }
                                
                                Text {
                                    text: "👨‍🍳 " + (selectedRecipe ? selectedRecipe.skill_level : "")
                                    color: "#00ff99"
                                    font.pixelSize: 16
                                    font.bold: true
                                }
                            }
                            
                            Row {
                                spacing: 20
                                
                                Text {
                                    text: selectedRecipe && selectedRecipe.cooked ? "✅ Cooked" : "⏳ Not cooked yet"
                                    color: selectedRecipe && selectedRecipe.cooked ? "#00ff99" : "#cccccc"
                                    font.pixelSize: 14
                                }
                                
                                Text {
                                    text: selectedRecipe && selectedRecipe.liked ? "⭐ Favorite" : "🤍 Not favorited"
                                    color: selectedRecipe && selectedRecipe.liked ? "#ffaa00" : "#cccccc"
                                    font.pixelSize: 14
                                }
                            }
                        }
                    }
                    
                    // Ingredients (only show if recipe selected)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: ingredientsColumn.height + 30
                        color: "#404040"
                        radius: 12
                        visible: selectedRecipe !== null
                        
                        Column {
                            id: ingredientsColumn
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12
                            
                            Text {
                                text: "📋 Ingredients"
                                color: "#ffffff"
                                font.pixelSize: 20
                                font.bold: true
                            }
                            
                            Column {
                                spacing: 6
                                Repeater {
                                    model: selectedRecipe ? selectedRecipe.ingredients : []
                                    
                                    Text {
                                        text: "• " + modelData
                                        color: "#cccccc"
                                        font.pixelSize: 14
                                    }
                                }
                            }
                        }
                    }
                    
                    // Instructions (only show if recipe selected)
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: instructionsColumn.height + 30
                        color: "#404040"
                        radius: 12
                        visible: selectedRecipe !== null
                        
                        Column {
                            id: instructionsColumn
                            anchors.fill: parent
                            anchors.margins: 20
                            spacing: 12
                            
                            Text {
                                text: "📝 Instructions"
                                color: "#ffffff"
                                font.pixelSize: 20
                                font.bold: true
                            }
                            
                            Column {
                                spacing: 10
                                Repeater {
                                    model: selectedRecipe ? selectedRecipe.instructions : []
                                    
                                    Text {
                                        text: (index + 1) + ". " + modelData
                                        color: "#cccccc"
                                        font.pixelSize: 14
                                        wrapMode: Text.WordWrap
                                        width: instructionsColumn.width - 40
                                    }
                                }
                            }
                        }
                    }
                    
                    // Action buttons (only show if recipe selected)
                    Row {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 20
                        visible: selectedRecipe !== null
                        
                        Rectangle {
                            width: 180
                            height: 50
                            color: cookThisMouseArea.pressed ? "#cc5500" : "#ff6b35"
                            radius: 25
                            
                            Text {
                                text: "🎤 Cook This Recipe"
                                color: "#ffffff"
                                font.pixelSize: 14
                                font.bold: true
                                anchors.centerIn: parent
                            }
                            
                            MouseArea {
                                id: cookThisMouseArea
                                anchors.fill: parent
                                onClicked: {
                                    if (selectedRecipe) {
                                        window.isCooking = true
                                        window.showStatus("Starting cooking: " + selectedRecipe.name)
                                        stackView.replace(cookingViewComponent)
                                    }
                                }
                            }
                        }
                        
                        Rectangle {
                            width: 120
                            height: 50
                            color: favoriteMouseArea.pressed ? "#cc8800" : "#ffaa00"
                            radius: 25
                            
                            Text {
                                text: selectedRecipe && selectedRecipe.liked ? "💔 Unfavorite" : "⭐ Favorite"
                                color: "#000000"
                                font.pixelSize: 14
                                font.bold: true
                                anchors.centerIn: parent
                            }
                            
                            MouseArea {
                                id: favoriteMouseArea
                                anchors.fill: parent
                                onClicked: {
                                    if (selectedRecipe) {
                                        selectedRecipe.liked = !selectedRecipe.liked
                                        window.showStatus(selectedRecipe.liked ? "Added to favorites!" : "Removed from favorites")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Functions
    function getFilteredRecipes() {
        if (currentFilter === "all") {
            return recipes
        } else if (currentFilter === "cooked") {
            return recipes.filter(recipe => recipe.cooked)
        } else if (currentFilter === "liked") {
            return recipes.filter(recipe => recipe.liked)
        }
        return recipes
    }
    
    function getRecipeIcon(mealType) {
        switch(mealType) {
            case "breakfast": return "🌅"
            case "lunch": return "🌞"
            case "dinner": return "🌙"
            case "snack": return "🍿"
            default: return "🍽️"
        }
    }
}

