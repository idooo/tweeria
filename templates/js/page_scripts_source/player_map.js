$(function(){
   $("#nearby-players").on("click",function(e){
       e.preventDefault();

       $.fancybox($("#nearby-popup"),{
           closeBtn:false,
           wrapCSS:"tweenk-popup",
           padding:0,
           helpers:{
               overlay:{
                   css:{
                       "background":"transparent"
                   }
               }
           }
       });
   });
});
