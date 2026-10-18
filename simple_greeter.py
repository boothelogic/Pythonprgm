def  greeter(name1):
     print("Hello, " +name1 ,end="!") 



name1=input("What's Your Good Name: ")
greeter(name1)

age=int(input("How Old Are You: "))
print("Hello, " +name1,"!","You Are ",age,"Years Old ?")

if age<18:
    print("you Are Not Eligible")
else:
      print("You Are Eligible For Whatever this is")
