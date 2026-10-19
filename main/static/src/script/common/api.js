window.apiCall = async function (method, url, params = {}, data = undefined) {
  const cleanParams = {};
  for (const key in params) {
    if (params[key] != null) {
      cleanParams[key] = params[key];
    }
  }

  const queryStr = new URLSearchParams(cleanParams).toString();
  const separator = url.indexOf('?') >= 0 ? '&' : '?';
  const fullUrl = queryStr ? `${url}${separator}${queryStr}` : url;

  try {
    const response = await fetch(fullUrl, {
      body: data ? JSON.stringify(data) : undefined,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      method: method,
    });

    let resultData;
    try {
      resultData = await response.json();
    } catch (err) {
      resultData = {error_thrown: err};
    }

    if (!response.ok || resultData.status !== 'success') {
      const error = Object.assign(
        {
          error_code: 'fetch_error',
          error_thrown: response.statusText,
          response: response,
        },
        resultData,
      );
      LOG('apiCall error', error);
      throw error;
    }

    let more = undefined;
    if (resultData.next_url) {
      more = () => apiCall(method, resultData.next_url);
    }

    return {more: more, result: resultData.result};
  } catch (errorThrown) {
    const error =
      errorThrown && errorThrown.error_code
        ? errorThrown
        : {
            error_code: 'fetch_error',
            error_thrown: errorThrown,
          };
    LOG('apiCall error', error);
    throw error;
  }
};
