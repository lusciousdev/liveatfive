const data = document.currentScript.dataset;

const getWhenUrl = data.getwhen;
const getStreaksUrl = data.getstreaks;
const getHistoryUrl = data.gethistory;
const getRecordUrl = data.getrecord;

var DateTime = luxon.DateTime;

var goalTime = DateTime.fromObject({ hour: 17, minute: 0, second: 0 }, { zone: "America/Los_Angeles"});
var padTime = DateTime.fromObject({ hour: 17, minute: 15, second: 0 }, { zone: "America/Los_Angeles"});

var isLive = false;
var wasLive = false;

function populateRecord(data)
{
  var onTime = parseInt(data["on-time"]);
  var early  = parseInt(data["early"]);
  var total  = parseInt(data["total"]);
  var late = total - onTime - early;

  var recordDiv = `{0} on-time, {1} early, {2} late.`.format(onTime, early, late);
  $("#record").html(recordDiv);
}

function populateStreaks(data)
{
  var onTime = parseInt(data["on-time"]);
  var early  = parseInt(data["early"]);
  var late   = parseInt(data["late"]);

  $("#longest-early").html(`Early: {0} `.format(early));
  $("#longest-on-time").html(`On-time: {0}`.format(onTime));
  $("#longest-late").html(`Late: {0}`.format(late));
}

function populateHistory(data)
{
  $("#history-table").html(`<tr class="table-header">
  <th>Date</th>
  <th>Time</th>
  <th>Offset</th>
  <th>Status</th>
</tr>`);

  var dict = data['streams']
  idx = 0;
  for (var key in dict)
  {
    var value = null;
    if (dict.hasOwnProperty(key))
    {
      value = dict[key];
    }

    var liveString = ""
    
    if (value["punctuality"] == 0)
    {
      liveString = "EARLY"
    }
    else if (value["punctuality"] == 1)
    {
      liveString = "ON TIME"
    }
    else
    {
      liveString = "LATE"
    }

    $("#history-table").append(`<tr>
  <th class="live-date">{0}</th>
  <th class="live-time">{1}</th>
  <th class="live-offset">{2}</th>
  <th class="live-status">{3}</th>
</tr>`.format(key, value["time"], (value["offset"] / 60.0).toLocaleString(undefined, { maximumFractionDigits: 1, minimumFractionDigits: 1 }), liveString));

    idx++;
  }
}

function populateAverageTime(data)
{
  $("#avg-time").html(data["average"]);
}

function getWeekdaySelection() 
{
  return $("#weekday-select").find(":selected").val();
}

function getMonthSelection() 
{
  return $("#month-select").find(":selected").val();
}

function getYearSelection() 
{
  return $("#year-select").find(":selected").val();
}

function updatePage()
{
  var weekdaySelection = getWeekdaySelection();
  var monthSelection = getMonthSelection();
  var yearSelection = getYearSelection();

  var recordUrl = getRecordUrl + "?weekday=" + weekdaySelection;
  var historyUrl = getHistoryUrl + "?weekday=" + weekdaySelection;

  if (monthSelection != "")
  {
    recordUrl = recordUrl + "&month=" + monthSelection;
    historyUrl = historyUrl + "&month=" + monthSelection;
  }

  if (yearSelection != "")
  {
    recordUrl = recordUrl + "&year=" + yearSelection;
    historyUrl = historyUrl + "&year=" + yearSelection;
  }

  AjaxGet(recordUrl, {}, populateRecord, handleAjaxError);
  AjaxGet(historyUrl, {}, populateHistory, handleAjaxError);
}

function handleAjaxError(data)
{
  console.log("~~~~~~~~~~~ERROR~~~~~~~~~~~~~~~~~~~")
  console.log(data);
}

$(window).on('load', function() {
  AjaxGet(getWhenUrl, {}, populateAverageTime, handleAjaxError);

  AjaxGet(getStreaksUrl, {}, populateStreaks, handleAjaxError);

  updatePage();

  $(".config-select").change(function() {
    updatePage()
  });
});