window.api_call = function(method, url, params, data, callback) {
  callback = callback || data || params;
  data = data || params;
  if (arguments.length === 4) {
    data = void 0;
  }
  if (arguments.length === 3) {
    params = void 0;
    data = void 0;
  }
  params = params || {};
  for (let k in params) {
    if (params[k] == null) {
      delete params[k];
    }
  }
  let separator = url.search('\\?') >= 0 ? '&' : '?';
  $.ajax({
    type: method,
    url: `${url}${separator}${$.param(params)}`,
    contentType: 'application/json',
    accepts: 'application/json',
    dataType: 'json',
    data: data ? JSON.stringify(data) : void 0,
    success(data) {
      if (data.status === 'success') {
        let more = void 0;
        if (data.next_url) {
          more = callback => api_call(method, data.next_url, {}, callback);
        }
        typeof callback === 'function' ? callback(void 0, data.result, more) : void 0;
      } else {
        typeof callback === 'function' ? callback(data) : void 0;
      }
    },
    error(jqXHR, textStatus, errorThrown) {
      let error = {
        error_code: 'ajax_error',
        text_status: textStatus,
        error_thrown: errorThrown,
        jqXHR,
      };
      try {
        if (jqXHR.responseText) {
          error = $.parseJSON(jqXHR.responseText);
        }
      } catch (_error) {
        error = _error;
      }
      LOG('api_call error', error);
      typeof callback === 'function' ? callback(error) : void 0;
    },
  });
};
