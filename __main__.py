from keychain import IO, Group, Key, KeyChain, User

keychain = KeyChain.load_csv("__scratch__/1.csv")
io = IO("./proto", "469891")
io.write(keychain)

# a = User("a","vggb")
# b = User("ab","vgwqgb")

# q = Key("kl,u",user_list=[a,b])
# g=Group("g",q)
