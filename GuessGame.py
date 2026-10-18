
print("""Welcome To Guess Game!Guess a Fun Word Starts With 'n'""")


word="nigga"
guess=''
guesscount=0
maxguesses=5
out_of_guesses=False
while guess!=word and not(out_of_guesses):
      if guesscount<maxguesses:
         guess=input("Type The guess:")
         print("Wrong Answer ! Try Again")
         guesscount+=1
      else:
          out_of_guesses=True


if  out_of_guesses:
    print("you are out of guesses!")
else:
    print("you win !")
