function onDragStart(event) {
    // Clear existing data from last transfer
    event
        .dataTransfer
        .clearData();

    // Set data of draggable id so we can append it to new dropzone
    event
        .dataTransfer
        .setData('text/plain', event.target.id);

    // Change the background of the dragged element
    event
        .currentTarget
        .style
        .backgroundColor = '#dddddd';

    // I think this helps stop firefox for trying to redirect to the id's value?
    event
        .dataTransfer
        .effectAllowed = 'move';

    //// We are getting the old dropzone by id, which before drag
    //// Should always be matching drag id
    // Get the placement id from the dragged item
    dragId = event.currentTarget.getAttribute('id')

    // Take just the number off the end
    dragNum = dragId.slice(-1);

    // Append the number to drop so we can set the value of the new dropzone
    dropId = 'drop' + dragNum;

    // Add drop capabiliies to old dropzone
    oldDrop = document.getElementById(dropId);
    oldDrop.setAttribute('ondragover', 'onDragOver(event);');
    // Get rid of old id so new drop zone can have it
    oldDrop.setAttribute('id', '');
}

function onDragEnd(event) {
    event
        .currentTarget
        .style
        .backgroundColor = 'white';
}

function onDragOver(event) {
    event.preventDefault();
}

function onDragEnter(event) {
    event
        .currentTarget
        .style
        .boxShadow = '0px 0px 7px #2999FF';
}

function onDragExit(event) {
    event
        .currentTarget
        .style
        .boxShadow = '0px 0px 0px white';
}

function onDrop(event) {
    event.preventDefault();

    // Get id passed from onDragStart
    const id = event
        .dataTransfer
        .getData('text');

    // Get dragged element
    const draggableElement = document.getElementById(id);

    // Get drop container
    const dropzone = event.target;

    // remove drop capabilities from new container
    // (So we can't drop two answers in)
    dropzone.setAttribute('ondragover', '');

    // Append draggable to drop container
    dropzone.appendChild(draggableElement);


    //// Making the container id match the drag id so that
    //// we can turn the drop capabilities back on if it's moved again
    // Take just the number off the end of drag id
    dragId = id.slice(-1);

    // Append the number to drop so we can set the value of the new dropzone
    dropId = 'drop' + dragId;

    // After drag is complete- drop id and drag id should have matching numbers
    dropzone.setAttribute('id', dropId);


    //// Making the drag name variable match the container name
    //// variables so we can check if the user guessed correctly
    // Get question(picture) name
    questionName = dropzone.getAttribute('name');

    // Get children of draggable, since they have the variable and value
    children = draggableElement.children;

    // Check that name is from picture box and not bank
    if (questionName) {
        // If so, take the number from question name
        // If the name attribute is 7 characters, the last character
        // is the number, take that
        if (questionName.length == 9) {
            idNum = questionName.slice(-1);
        }
        // Else if the name attribute is 8 characters, the last  two characters
        // are the number, take that
        else if (questionName.length == 10) {
            idNum = questionName.slice(-2);
        }
        // Otherwise, something went wrong
        else {
            console.log("Something went wrong with making the answer id");
        }

        answerName = 'answer' + idNum;
        // And make the draggable children match
        children[0].setAttribute('for', answerName);
        children[1].setAttribute('id', answerName);
        children[1].setAttribute('name', answerName);
    }
}

/////////////////////////////////////////////////////////////////////////////////////////////
// Gallery and Favorites pages

// Makes the artwork description visible on gallery page
function onMouseOver(event) {
    // Get image url
    let element = event.currentTarget;
    let image = element.parentNode.getAttribute('style');
    // Get rid of 'background-image: '
    image = image.slice(17);

    // Create the rest of the attribute string
    let backgroundImage = 'background-image: ';
    let darken = 'linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), ';

    // Concatenate strings
    let darkImage = backgroundImage + darken + image;

    // Set style
    element.parentNode.setAttribute('style', darkImage);
}

function onMouseOut(event) {
    // Get darkened image
    let element = event.currentTarget;
    let image = element.parentNode.getAttribute('style');

    if (image.includes('linear')) {
        // only keep the url
        image = image.slice(78);

        // Concatenate with 'background-image: '
        let backgroundImage = 'background-image: ';
        let revertedImage = backgroundImage + image;

        // Set style
        element.parentNode.setAttribute('style', revertedImage);
    }
}

//////////////////////////////////////////////////////////////////////////////////////////
// Settings page

// Changes the size and number of preview boxes according to grid size
function gridChange(selectValue) {
    // Get preview container where we'll preview the quiz grid
    let preview = document.getElementById('preview-container');
    // Get background color from current children
    let background = preview.firstChild.getAttribute('style');

    // If there is a hidden info div
    if (!preview.firstChild.getAttribute('class')) {
        // Delete display attribute
        background = background.slice(15, background.length);
    }

    // Remove all children from preview box
    preview.innerHTML = '';
    // Get gridsize
    let size = selectValue;
    // Assign class for boxes
    if (size == 2) {
        classAttr = 'twoBy';
    }
    else if (size == 3) {
        classAttr = 'threeBy';
    }
    else if (size == 4) {
        classAttr = 'fourBy';
    }
    else {
        classAttr = 'fiveBy';
    }
    // Get number of boxes in grid
    size = size * size;

    for (let i = 0; i < size; i++) {
        // Create child divs to append
        let box = document.createElement('div');
        // Set class for box size
        box.setAttribute('class', classAttr);
        // Set style for background color
        box.setAttribute('style', background);
        // Append to preview div
        preview.appendChild(box);
    }
}

// Changes the color of the preview boxes according to difficulty
function diffChange(selectValue) {
    // Get preview container where we'll preview the quiz grid
    let preview = document.getElementById('preview-container');
    // Get class attribute from first child
    let classAttr = preview.firstChild.getAttribute('class');
    // If there is a hidden info div
    if (!preview.firstChild.getAttribute('class')) {
        // Get old grid size
        classAttr = preview.firstChild.getAttribute('id');

    }
    // Assign size based on class
    if (classAttr == 'twoBy') {
        size = 2;
    } else if (classAttr == 'threeBy') {
        size = 3;
    } else if (classAttr == 'fourBy') {
        size = 4;
    } else {
        size = 5;
    }
    // Remove all children from preview box
    preview.innerHTML = '';
    // Set background color based on difficulty
    let difficulty = selectValue;
    let color;
    if (difficulty == 0.75) {
        color = 'background-color: #add8e6';
    }
    else if (difficulty == 0.5) {
        color = 'background-color: #90ee90';
    }
    else if (difficulty == 0.25) {
        color = 'background-color: #FFBE7D';
    }
    else {
        color = 'background-color: #FF7D7D';
    }

    // Get number of boxes in grid
    size = size * size;

    for (let i = 0; i < size; i++) {
        // Create child divs to append
        let box = document.createElement('div');
        // Set class for box size
        box.setAttribute('class', classAttr);
        // Set style for background color
        box.setAttribute('style', color);
        // Append to preview div
        preview.appendChild(box);
    }
}

// This sets the background to heart icons for the favorites grid preview
function favGrid(selectValue) {
    // Get preview container where we'll preview the quiz grid
    let preview = document.getElementById('preview-container');
    // Create hidden element to save difficulty color
    let diff = document.createElement('div');
    // Get old color from current children
    let color = preview.firstChild.getAttribute('style');
    // Get old gridSize from current children
    let gridSize = preview.firstChild.getAttribute('class')
    // Add display: none attribute to style
    color = 'display: none; ' + color;
    diff.setAttribute('style', color);
    // Save gridSize in id
    diff.setAttribute('id', gridSize);

    // Remove all children from preview box
    preview.innerHTML = '';
    // Get gridsize
    let size = selectValue;
    let classAttr;
    // Change background image size based on grid size
    let backgroundSize;
    // Assign class for boxes
    if (size == 2) {
        classAttr = 'twoBy';
        backgroundSize = 'background-size: 190px 190px;';
    }
    else if (size == 3) {
        classAttr = 'threeBy';
        backgroundSize = 'background-size: 120px 120px;';
    }
    else if (size == 4) {
        classAttr = 'fourBy';
        backgroundSize = 'background-size: 90px 90px;';
    }
    else {
        classAttr = 'fiveBy';
        backgroundSize = 'background-size: 70px 70px;';
    }
    // Contruct rest of style attribute
    style = backgroundSize + ' background-image: url(\'/static/images/heartOutline.png\'); background-color: #FFD2DA;';
    // Get number of boxes in grid
    size = size * size;

    // Add hidden child to keep track of color
    preview.appendChild(diff);

    for (let i = 0; i < size; i++) {
        // Create child divs to append
        let box = document.createElement('div');
        // Set class for box size
        box.setAttribute('class', classAttr);
        // Set style for background color
        box.setAttribute('style', style);
        // Append to preview div
        preview.appendChild(box);
    }
}
