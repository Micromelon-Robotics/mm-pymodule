<%! 
    from pdoc.html_helpers import minify_css 
%> 
<%def name="homelink()" filter="minify_css"> 
    .homelink img { 
        max-width:20%; 
        max-height: 5em; 
        margin: auto; 
        margin-bottom: .3em; 
    } 
</%def> 
 
<style>${homelink()}</style>