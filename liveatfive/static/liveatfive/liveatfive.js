const data = document.currentScript.dataset;

const isLiveUrl = data.islive;
const getRecordUrl = data.getrecord;

var DateTime = luxon.DateTime;

var apiUrl = "https://five.luscious.dev"
var goalTime = DateTime.fromObject({ hour: 17, minute: 0, second: 0 }, { zone: "America/Los_Angeles"});
var padTime = DateTime.fromObject({ hour: 17, minute: 15, second: 0 }, { zone: "America/Los_Angeles"});
var year = goalTime.year;

var isLive = false;
var wasLive = false;

function populateRecord(data)
{
  var statusString = "early";
  if (data['streak-status'] == 1)
  {
    statusString = "on time";
  }
  else if (data['streak-status'] == 2)
  {
    statusString = "late";
  }

  var recordDiv = `itswill has been on time for {0} out of the {1} streams since January 1st, {5}.
  <br>
  itswill has been early for {2} out of the {1} streams since January 1st, {5}
  <br>
  itswill has been {3} {4} times in a row.`.format(data["on-time"], data["total"], data["early"], statusString, data['streak'], year);
  $("#record").append(recordDiv);
}

function populateIsLive(data)
{
  isLive = (data['live'] == 1);
  wasLive = (data['waslive'] == 1);
  setIsLiveText();
}

function getTimeString(diffObj)
{
  var hourStr = diffObj['hours'].toString();
  var minStr  = diffObj['minutes'].toString().padStart(2, '0');
  var secStr  = diffObj['seconds'].toString().padStart(2, '0');
  
  var timeStr = "";
  if (diffObj['hours'] > 0)
  {
    timeStr = "{0}h {1}m {2}s".format(hourStr, minStr, secStr);
  }
  else if (diffObj['minutes'] > 0)
  {
    timeStr = "{0}m {1}s".format(minStr, secStr);
  }
  else
  {
    timeStr = "{0}s".format(secStr);
  }

  return timeStr;
}

function setIsLiveText()
{
  $("#islive").empty();
  var now = DateTime.local().setZone("America/Los_Angeles");

  if (isLive)
  {
    $("#islive").append(`He's live right now. Go watch.`);
  }
  else if (wasLive)
  {
    $("#islive").append(`Stream is over.`);
  }
  else if (now.toFormat('c') == 4)
  {
    $("#islive").append(`It's Thursday. Chances of a stream are low.`);
  }
  else
  {
    if (goalTime > now)
    {
      var til5 = goalTime.diff(now, ['hours', 'minutes', 'seconds', 'milliseconds']).toObject();
      var timeStr = getTimeString(til5);
      $("#islive").append(`He <i>should</i> be live in {0}.`.format(timeStr));
    }
    else if (padTime > now)
    {
      var til515 = padTime.diff(now, ['hours', 'minutes', 'seconds', 'milliseconds']).toObject();
      var timeStr = getTimeString(til515);
      $("#islive").append(`Respect the 15 minute buffer. We still have {0} left before he's late.`.format(timeStr));
    }
    else
    {
      var since5 = now.diff(padTime, ['hours', 'minutes', 'seconds', 'milliseconds']).toObject();
      var timeStr = getTimeString(since5);
      $("#islive").append(`He <i>should've</i> been live {0} ago...`.format(timeStr));
    }
  }
}

function checkIsLive()
{
  AjaxGet(isLiveUrl, {}, populateIsLive, handleAjaxError);
}

function handleAjaxError(data)
{
  console.log("~~~~~~~~~~~ERROR~~~~~~~~~~~~~~~~~~~")
  console.log(data);
}

$(window).on('load', function() {
  var recordUrl = getRecordUrl
  AjaxGet(recordUrl, {}, populateRecord, handleAjaxError);
  checkIsLive();

  var intervalId = setInterval(function() { checkIsLive(); }, 15000);
  var otherInterval = setInterval(function() { setIsLiveText(); }, 500);
});