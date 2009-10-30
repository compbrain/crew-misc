$().ajaxSend(function(r,s){
  $("#loadingbar").show();
});

$().ajaxStop(function(r,s){
  $("#loadingbar").fadeOut("fast");
});

function setstate(row) {
  $('#job-'+row.id).attr('class',row.state);
}

function AddJob(row) {
  var content = '<td>' + row.id + '</td><td>' + row.physicaldest +
                '</td><td>' + row.finisher + '</td>' + '<td>' + row.owner
                + '</td><td>' + row.title + '</td><td>' + row.state + '</td>';
  if ($('#job-'+row.id).length > 0) {
    $('#job-'+row.id).replaceWith('<tr id="job-'+row.id+'">'+content+'</tr>');
    setstate(row);
    return 1;
  }
  $('#printjobs tbody').prepend('<tr id="job-' + row.id +
                                '" style="display:none">' + content + '</tr>');
  setstate(row);
  $("#job-"+row.id).fadeIn(1000);
}

function cleanUp(ids) {
  $('#joblist TR').each(function() {
    var tr = $(this);
    var idstr = tr.attr('id');
    if (idstr.search('job') != -1) {
      idnum = parseInt(idstr.split('-')[1]);
      if (ids.indexOf(idnum) == -1) {
        tr.fadeOut(1000, function() {$(this).remove();});
      }
    }
  });
}

function getData() {
  var tmpdate = new Date();
  tmp = '?nocache=' + tmpdate.getTime();
  $.getJSON('json/'+tmp, function(data){
    var ids = new Array;
    data.sort(function(one,two) { return one.id - two.id; });
    $.each(data, function(i, item) {
      AddJob(item);
      ids.push(item.id);
      });
    cleanUp(ids);
    });
}

function periodicupdate() {
  getData();
  setTimeout("periodicupdate()", 5001);
}

$(document).ready(function(){ periodicupdate(); });
