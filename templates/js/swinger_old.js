
let asof = Array()
let margin = []
let colors = []
let days = []
// Get the elements from HTML
const todoInput = document.getElementById('todoInput');
const addTodoButton = document.getElementById('addTodoButton');
const todoList = document.getElementById('todoList');
const average = array => array.reduce((a, b) => a + b) / array.length;

function gettickers() {
  try {
    document.body.style.cursor = 'crosshair';
    let tickers = localStorage.getItem("tickers").split(",")
    tickers.forEach(tick => {
      console.log(tick)
      document.getElementById("todoInput").value = tick
      addTodo()
    })
  }
  catch (e) {
    console.log(e)
  }
  document.body.style.cursor = 'default';
}

function convertDate() {
  a = Date()
  b = a.split(" ")[4]
  c = b.split(":")
  c[0] = c[0] > 12 ? c[0] - 12 : c[0]
  tim = c[0] + ":" + c[1]
  return tim
}

function refreshDiv(myDiv, content) {
  var div = document.getElementById(myDiv);
  // Fade out the div
  div.style.opacity = 0;

  // Wait for the transition to finish, then change the content and fade in
  setTimeout(function () {
    div.innerHTML = content; // change the content
    div.style.opacity = 1; // fade in
  }, 800); // this delay should be the same as the transition duration in the CSS
}

function getStatus(tick) {
  document.body.style.cursor = 'crosshair';
  const url = "https://fleminganalytic.com/swing/status/" + tick
  let resp = ""
  try {
    fetch(url, {
      mode: 'cors', headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })
      .then(ret => ret.json())
      .then(data => {
        data = (JSON.parse(data))

        sta = data["data"][0]['flag']
        try {
          refreshDiv(tick + '_c1', tick)
          refreshDiv(tick + '_c2', sta)
          refreshDiv(tick + '_c3', data["data"][0]['close'].toFixed(2))
          refreshDiv(tick + '_c4', data["data"][0]['l5'].toFixed(2))
          setTimeout(getStatus, 30000, tick)
        }
        catch (e) {
          console.log(e)
        }
      })
  }
  catch (e) {
    console.log(e)
  }
  document.body.style.cursor = 'default';
}

function addTodoCol(id) {
  let col = document.createElement('div');
  col.id = id
  col.classList.add("col")
  col.classList.add("text-center")
  col.innerText = "";

  return col
}

function get_buys(tick) {

  asof = []


  margin = []
  days = []
  colors = []
  document.body.style.cursor = 'crosshair';
  const url = "https://fleminganalytic.com/swing/getbuys/" + tick
  let resp = ""
  try {
    fetch(url, {
      mode: 'cors', headers: {
        'Access-Control-Allow-Origin': '*'
      }
    })
      .then(ret => ret.json())
      .then(data => {
        data = (JSON.parse(data))

        try {
          data['data'].forEach(element => {

            asof.push(element.asof.substring(5) + ' (' + element.days.toString() + 'd)')
            margin.push(element.margin)
            colors.push(element.color)
            days.push(element.days)
          }

          )
        }
        catch (e) {
          console.log(e)
        }
        plot_buys(tick)
      })
  }
  catch (e) {
    console.log(e)
  }


  document.body.style.cursor = 'default';
}

function plot_buys(tick) {
  document.getElementById("chart").innerHTML = ""
  var pdata = [
    {
      x: asof,
      y: margin,
      marker: {
        color: colors,
        size: 12
      },
      type: 'bar',
      text: days,

    }
  ];
    try{
  Plotly.newPlot('chart', pdata, { title: tick + ' Trade History\n' + average(margin).toFixed(2) + '% Avg. Margin', xaxis: { title: 'Date (Days Held)' }, yaxis: { title: 'Margin (%)' } }, { responsive: true, displayModeBar: false, scrollZoom: true, modeBarButtonsToRemove: ['toImage', 'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines', 'hoverClosestPie', 'hoverClosest3d', 'hoverClosestGl2d', 'hoverClosestGeo', 'hoverClosestGl2d', 'toggleHover', 'resetViews', 'toggleSpikelines', 'resetViewMapbox'] });
    }
    catch(e){
      document.getElementById("chart").innerHTML = "No Data for "+tick
}
}

// Function to add a new todo item
function addTodo() {
  document.body.style.cursor = 'crosshair';
  const todoText = todoInput.value.toUpperCase();
  let row = addtodorow(todoText)
  
  
  ttext=document.createElement('span')
  ttext.classList.add('tooltiptext')
  ttext.innerText='Click for chart'
  
  col1=addTodoCol(todoText + "_c1")
  col1.classList.add('tooltip');
  col1.addEventListener('click', function () {
    get_buys(todoText)
  });
  col1.appendChild(ttext)
  
  row.appendChild(col1)
  
  



  
  
  
  row.appendChild(addTodoCol(todoText + "_c2"))
  row.appendChild(addTodoCol(todoText + "_c3"))
  row.appendChild(addTodoCol(todoText + "_c4"))

  col5 = addTodoCol(todoText + "_c5")

  col5.innerHTML = '<i class="bi bi-bar-chart-fill icon-blue"></i>';

  
  col5.addEventListener('click', function () {
    plot_buys(todoText)
  });

    row.appendChild(col5)
  
  col6 = addTodoCol(todoText + "_c6")

  col6.innerHTML = '<i class="bi bi-trash icon-red"></i>';

  
  col6.addEventListener('click', function () {
    todoList.removeChild(row);
    savetickers()
  });

  row.appendChild(col6)

  todoList.appendChild(row);
  savetickers()
  setTimeout(getStatus, 100, todoText)

  todoInput.value = '';
}

// Add event listener for the add button
addTodoButton.addEventListener('click', addTodo);

function createheader(id) {
  h = document.createElement('div');
  h.classList.add('col');
  h.classList.add('d-flex')
  h.classList.add('justify-content-center')
  h.innerText = id
  h.style.fontWeight = 'bold';
  return h
}

function createheaders(row) {
  row.appendChild(createheader("Ticker"))
  row.appendChild(createheader("Name"))
  row.appendChild(createheader("Count"))
  row.appendChild(createheader("AvgRet"))
  row.appendChild(createheader("Stdev"))
  return row
}

function addtodorow(id) {
  row = document.createElement('div');
  row.classList.add('row');
  row.classList.add('todo-item');
  row.classList.add('ticker-row');
  row.id = id
  return row
}

function savetickers() {
  let tickers = []
  document.querySelectorAll('.ticker-row').forEach(row => {
    tickers.push(row.id)
  })
  localStorage.setItem("tickers", tickers)
}

function addrow(id) {
  row = document.createElement('div');
  row.classList.add('row');
  row.id = id
  return row
}

function addcolumn(value) {
  col = document.createElement('div');
  col.classList.add('col');
  col.innerText = value.toUpperCase();
  col.classList.add('align-center');
  col.classList.add('d-flex')
  col.classList.add('justify-content-center')
  return col
}



function getbuys() {
  const url = "https://fleminganalytic.com/swing/buys"
  let resp = ""
  fetch(url, {
    mode: 'no-cors', headers: {
      'Access-Control-Allow-Origin': '*'
    }
  })
    .then(ret => ret.json())
    .then(data => {
      data = (JSON.parse(data))
      try {
        x = data["data"]
        const candidates = document.getElementById('candidates');
        candidates.innerHTML = ""
        row = addrow("r0")
        createheaders(row)
        candidates.appendChild(row);
        if (x.length == 0) candidates.innerHTML = "No active candidates"
        for (i = 0; i < x.length; i++) {
          row = addrow("r" + i)
          tick = x[i]['tick']
          name = x[i]['name'].substring(0, 10)
          count = x[i]['count']
          avgret = x[i]['avgret']
          stdev = x[i]['stdev']
          row.appendChild(addcolumn(tick))
          row.appendChild(addcolumn(name))
          row.appendChild(addcolumn(count.toString()))
          row.appendChild(addcolumn(avgret.toString()))
          row.appendChild(addcolumn(stdev.toString()))
          candidates.appendChild(row);
        }
      }
      catch (e) {
        console.log(e.message)
      }
    })
}

getbuys()
setInterval(getbuys, 3600000)
gettickers()


