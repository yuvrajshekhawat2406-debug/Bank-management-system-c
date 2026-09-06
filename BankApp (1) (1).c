#include <stdio.h>
#include <stdlib.h>
#include <string.h>


typedef struct {
    int account_number;
    char name[100]; // Assuming a maximum name length of 100
    float balance;
} Account;

void pause_c() {
    for (long long i = 1; i <= 5000000000; i++);
}

int is_user_exist_c(int ac_no) {
    FILE *ifs = fopen("bank.txt", "r");
    if (ifs != NULL) {
        Account temp_account;
        while (fscanf(ifs, "%d %99[^-]-%f", &temp_account.account_number, temp_account.name, &temp_account.balance) == 3) {
            if (temp_account.account_number == ac_no) {
                fclose(ifs);
                return 1;
            }
        }
        fclose(ifs);
        return 0;
    }
    return 0;
}

void add_new_user_details_c() {
    system("cls");
    int ac_no;

    printf("\nInput details of new user\n");

    printf("\nEnter account no: ");
    scanf("%d", &ac_no);

    if (!is_user_exist_c(ac_no)) {
        FILE *ofs = fopen("bank.txt", "a");
        if (ofs != NULL) {
            Account new_account;
            new_account.account_number = ac_no;
            new_account.balance = 0;

            printf("\nEnter name: ");
            getchar(); // Consume newline left by scanf
            fgets(new_account.name, sizeof(new_account.name), stdin);
            new_account.name[strcspn(new_account.name, "\n")] = 0; // Remove trailing newline

            fprintf(ofs, "%d %s-%f\n", new_account.account_number, new_account.name, new_account.balance);

            fclose(ofs);

            printf("\nNew user account details are added successfully\n\n");
            pause_c();
        }
        else {
            printf("Error opening file\n");
            pause_c();
        }
    }else{
        printf("\n\nDetails of %d is already added!!",ac_no);
        pause_c();
    }
}

void view_user_account_details_c(int ac_no) {
    FILE *ifs = fopen("bank.txt", "r");
    if (ifs != NULL) {
        Account temp_account;
        while (fscanf(ifs, "%d %99[^-]-%f", &temp_account.account_number, temp_account.name, &temp_account.balance) == 3) {
            if (temp_account.account_number == ac_no) {
                printf("\nYour Account Details\n");
                printf("Account No: %d\n", temp_account.account_number);
                printf("Name: %s\n", temp_account.name);
                printf("Balance: Rs. %.2f\n\n", temp_account.balance);
                pause_c();
                break;
            }
        }
        fclose(ifs);
    }
}

void view_user_balance_c(int ac_no) {
    FILE *ifs = fopen("bank.txt", "r");
    if (ifs != NULL) {
        Account temp_account;
        while (fscanf(ifs, "%d %99[^-]-%f", &temp_account.account_number, temp_account.name, &temp_account.balance) == 3) {
            if (temp_account.account_number == ac_no) {
                printf("\nBalance: Rs. %.2f\n\n", temp_account.balance);
                pause_c();
                break;
            }
        }
        fclose(ifs);
    }
}

void deposit_amount_c(int ac_no) {
    int amount;
    FILE *ifs = fopen("bank.txt", "r");
    FILE *ofs = fopen("new.txt", "w");

    if (ifs != NULL && ofs != NULL) {
        Account temp_account;
        while (fscanf(ifs, "%d %99[^-]-%f", &temp_account.account_number, temp_account.name, &temp_account.balance) == 3) {
            fprintf(ofs, "%d %s-", temp_account.account_number, temp_account.name);
            if (temp_account.account_number == ac_no) {
                printf("\nEnter the amount: Rs. ");
                scanf("%d", &amount);
                temp_account.balance += amount;
                printf("\nRs. %d is deposited successfully\n\n", amount);
                pause_c();
            }
            fprintf(ofs, "%.2f\n", temp_account.balance);
        }
        fclose(ifs);
        fclose(ofs);

        remove("bank.txt");
        rename("new.txt", "bank.txt");
    }
}

void withdraw_amount_c(int ac_no) {
    int amount;
    FILE *ifs = fopen("bank.txt", "r");
    FILE *ofs = fopen("new.txt", "w");

    if (ifs != NULL && ofs != NULL) {
        Account temp_account;
        while (fscanf(ifs, "%d %99[^-]-%f", &temp_account.account_number, temp_account.name, &temp_account.balance) == 3) {
            fprintf(ofs, "%d %s-", temp_account.account_number, temp_account.name);
            if (temp_account.account_number == ac_no) {
                if (temp_account.balance > 0) {
                    printf("\nEnter the amount: Rs. ");
                    scanf("%d", &amount);
                    if (amount <= temp_account.balance) {
                        temp_account.balance -= amount;
                        printf("\nRs. %d is withdrawn successfully\n\n", amount);
                        pause_c();
                    } else {
                        printf("\nInvalid transaction\n\n");
                        pause_c();
                    }
                } else {
                    printf("\nInsufficient balance\n\n");
                    pause_c();
                }
            }
            fprintf(ofs, "%.2f\n", temp_account.balance);
        }
        fclose(ifs);
        fclose(ofs);

        remove("bank.txt");
        rename("new.txt", "bank.txt");
    }
}

int main() {
    int ch, ac_no;
    do {
        system("cls");
        printf("\n-------- Welcome to MyBank App --------\n");
        printf("Enter 1 to create new user account\n");
        printf("Enter 2 to use existing user account\n");
        printf("Enter 3 to exit from app\n");
        printf("Enter your choice: ");
        scanf("%d", &ch);
        switch (ch) {
            case 1:
                add_new_user_details_c();
                break;
            case 2:
                system("cls");
                printf("\nEnter account number: ");
                scanf("%d", &ac_no);
                if (is_user_exist_c(ac_no)) {
                    do {
                        system("cls");
                        printf("\n----- Here are your options -----\n");
                        printf("Enter 1 to view your account details\n");
                        printf("Enter 2 to view your balance\n");
                        printf("Enter 3 to deposit an amount\n");
                        printf("Enter 4 to withdraw an amount\n");
                        printf("Enter 5 to exit from app\n");
                        printf("Enter your choice: ");
                        scanf("%d", &ch);
                        switch (ch) {
                            case 1:
                                view_user_account_details_c(ac_no);
                                break;
                            case 2:
                                view_user_balance_c(ac_no);
                                break;
                            case 3:
                                deposit_amount_c(ac_no);
                                break;
                            case 4:
                                withdraw_amount_c(ac_no);
                                break;
                            case 5:
                                exit(0);
                            default:
                                printf("\nWrong choice entered\n");
                        }
                    } while (1);
                } else {
                   printf("\nInvalid Account Number\n\n");
                    pause_c();
            }
        case 3:
            exit(0);
        default:
            printf("\nWrong Choice Entered\n");
            pause_c();
        }
    }while(1);
}
