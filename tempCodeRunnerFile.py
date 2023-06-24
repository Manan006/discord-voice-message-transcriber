    def run(self,token,close_func,*args,**kwargs):
        self.close_func = close_func
        try:
            self.super.run(token,*args,**kwargs)
        except Exception as e:
            print(e)
        sys.exit(1)

    async def close(self,*args,**kwargs):
        await self.close_func()
        await self.super.close(*args,**kwargs)
