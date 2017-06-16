(function() {
	tinymce.PluginManager.requireLangPack('mformulas');

	tinymce.create('tinymce.plugins.MFormulasPlugin', {
		init : function(ed, url) {
			ed.addCommand('mceMFormulas', function() {
				ed.windowManager.open({
					file : url + '/mformulas.html',
					width : 320 + parseInt(ed.getLang('mformulas.delta_width', 0)),
					height : 130 + parseInt(ed.getLang('mformulas.delta_height', 0)),
					inline : 1
				}, {
					plugin_url : url
				});
			});

			ed.addButton('mformulas', {
				title : 'mformulas.desc',
				cmd : 'mceMFormulas',
				image : url + '/img/mformulas.gif'
			});

			ed.onNodeChange.add(function(ed, cm, n) {
				cm.setActive('mformulas', n.nodeName == 'IMG');
			});
		},

		createControl : function(n, cm) {
			return null;
		},

		getInfo : function() {
			return {
				longname : 'MFormulas plugin',
				author : 'Tomuniversal',
				authorurl : 'http://web.tomuniversal.ru',
				infourl : 'http://web.tomuniversal.ru',
				version : "1.0"
			};
		}
	});

	tinymce.PluginManager.add('mformulas', tinymce.plugins.MFormulasPlugin);
})();