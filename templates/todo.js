// Get the elements from HTML
const todoInput = document.getElementById('todoInput');
const addTodoButton = document.getElementById('addTodoButton');
const todoList = document.getElementById('todoList');

// Function to add a new todo item
function addTodo() {
  const todoText = todoInput.value;

  // Create new todo item
  const newTodo = document.createElement('li');
  newTodo.innerText = todoText;
  newTodo.classList.add('todo-item');

  // Add a delete button for the new item
  const deleteButton = document.createElement('button');
  deleteButton.innerText = 'Delete';
  deleteButton.addEventListener('click', function() {
    todoList.removeChild(newTodo);
  });
  newTodo.appendChild(deleteButton);

  // Add the new todo item to the list
  todoList.appendChild(newTodo);

  // Clear the input box
  todoInput.value = '';
}

// Add event listener for the add button
addTodoButton.addEventListener('click', addTodo);
