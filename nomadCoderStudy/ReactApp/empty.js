function solution(arr) {
  var sum = 0;

  for (var i = 0; i < arr.length; i++) {
    //arr.length <= x  < o
    sum += arr[i];
  }

  return sum / arr.length;
}


function solution(arr) {
  var max = 0;

  for (var i = 0; i < arr.length; i++) {
    if (arr[i] > max) {
        //< > 교체
      max = arr[i];
    }
  }

  return max;
}


function solution(str) {
  var result = "";

  for (var i = str.length-1; i > 0; i--) {
    //조건문 범위 조정
    result -= str[i];
  }

  return result;
}


function solution(arr) {
  var count = 0;

  for (var i = 0; i < arr.length; i++) {
    if (arr[i] % 2 ===0) {
        //짝수는 %2===0
      count++;
    }
  }

  return count;
}


function solution(arr) {
  var min = arr[0];
  var index = 0;

  for (var i = 1; i < arr.length; i++) {
    if (arr[i] > min) {
      min = arr[i];
      index = min;
      //i => min
    }
  }

  return index;
}