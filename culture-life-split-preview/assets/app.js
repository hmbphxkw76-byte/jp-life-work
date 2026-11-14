// assets/app.js — tab switching + line-count comparison chart
(function () {
  // ---------- Tabs ----------
  var tabbar = document.getElementById('tabbar');
  var tabs = ['t0', 't1', 't2', 't3', 't4', 't5'];

  function activate(id) {
    tabs.forEach(function (t) {
      document.getElementById(t).hidden = (t !== id);
    });
    var btns = tabbar.querySelectorAll('button');
    btns.forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-tab') === id);
    });
  }

  tabbar.addEventListener('click', function (e) {
    var btn = e.target.closest('button');
    if (btn) activate(btn.getAttribute('data-tab'));
  });

  // Doc summary cards jump to preview section and switch tab
  document.querySelectorAll('.dcard[data-tab]').forEach(function (card) {
    card.addEventListener('click', function () {
      activate(card.getAttribute('data-tab'));
    });
  });

  // ---------- Chart: lines before/after split ----------
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();

  var el = document.getElementById('chart-lines');
  if (el && window.echarts) {
    var chart = echarts.init(el, null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      grid: { top: 30, left: 24, right: 60, bottom: 24, containLabel: true },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        appendToBody: true,
        formatter: function (params) {
          var p = params[0];
          return p.name + '<br/>约 ' + p.value + ' 行';
        }
      },
      xAxis: {
        type: 'category',
        data: ['拆分前\n单文件', '00 导航', '01 职场文化', '02 生活指南', '03 医疗健康', '04 住房安家', '05 社会融入'],
        axisLabel: { color: muted, fontSize: 12, interval: 0, lineHeight: 18 },
        axisLine: { lineStyle: { color: rule } },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'value',
        name: '行数',
        nameTextStyle: { color: muted },
        axisLabel: { color: muted },
        splitLine: { lineStyle: { color: rule } }
      },
      series: [{
        type: 'bar',
        barWidth: '46%',
        data: [
          { value: 561, itemStyle: { color: accent2 } },
          { value: 55, itemStyle: { color: accent } },
          { value: 40, itemStyle: { color: accent } },
          { value: 75, itemStyle: { color: accent } },
          { value: 90, itemStyle: { color: accent } },
          { value: 55, itemStyle: { color: accent } },
          { value: 30, itemStyle: { color: accent } }
        ],
        itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: {
          show: true,
          position: 'top',
          color: ink,
          fontWeight: 600,
          formatter: '{c} 行'
        }
      }]
    });
    window.addEventListener('resize', function () { chart.resize(); });
  }
})();
