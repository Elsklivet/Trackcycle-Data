import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.*;

/* This file will determine how many times the GPS turned on given the data file for a single ride.
 * It will also determine how much the phone battery dropped throughout the duration of the ride.
 * 
 * USAGE:
 *      To use this file first cd into the file directory, then run "javac NumCycles.java" to compile,
 *  and finally run "java NumCycles" to run the script.
 *      You will be asked to enter the name of the file you want to analyze. Enter the file name and make sure
 *  to add ".txt" at the end.
 */

public class NumCycles {
    public static void main(String[] cheese) throws IOException{ 
        Scanner scan = new Scanner(System.in);
        System.out.print("What file would you like to analyze: ");
        String fileName = scan.nextLine();

        FileReader fr = new FileReader(fileName);
        BufferedReader br = new BufferedReader(fr);
        int numCycles = 0;
        String line = br.readLine();
        double startBat = 0.0;
        double endBat = 0.0;
        double currBat = 0.0;

        
        while(line != null){
            if(line.equals("--GPS STARTED--"))
                numCycles++;
            if(!Character.isDigit(line.charAt(0))){
                line = br.readLine();
                continue;
            }
            currBat = Double.parseDouble(line.split(",")[15]);
            if(startBat == 0.0 && currBat > 0.0)
                startBat = currBat;

            line = br.readLine();
        }

        endBat = currBat;
        System.out.println("\n\n\n\n\nThe GPS turned on " + numCycles + " times.");
        System.out.println("Change in battery: " + (startBat-endBat) + "\n\n\n\n\n");
        br.close();
        scan.close();
    }
}
