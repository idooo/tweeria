/* global module:false */
module.exports = function(grunt) {

	// Project configuration
	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'),

		uglify: {
            plugins: {
                'src': 'templates/js/plugins/*.js',
                'dest': 'templates/js/plugins.js'
            },
            page_scripts: {
              files: [
                {
                  expand: true,
                  cwd: 'templates/js/page_scripts_source/',
                  src: ['**/*.js'],
                  dest: 'templates/js/page_scripts/'
                }
              ]
            }
		},

        sass: {
			modern: {
				files: {
					'templates/style/tweeria.css' : 'templates/src/scss/tweeria.scss'
				}
			}
		},

        cssmin: {
            modern: {
				files: {
					'templates/style/tweeria.css' : 'templates/style/tweeria.css'
				}
			},
            legacy: {
              files: [
                {
                  expand: true,
                  cwd: 'templates/src/css/',
                  src: ['*.css'],
                  dest: 'templates/style/'
                }
              ]
            }
        }

	});

	// Dependencies
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-cssmin');
	grunt.loadNpmTasks('grunt-contrib-uglify' );

	// Default task
	grunt.registerTask( 'default', [ 'sass', 'uglify', 'cssmin' ] );

	// Theme task
	grunt.registerTask( 'styles', [ 'sass' ] );

};
