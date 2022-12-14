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
 *      The program will also ask for the azimuth threshold used during the ride.
 */

public class NumCycles {
    public static void main(String[] cheese) throws IOException{ 
        Scanner scan = new Scanner(System.in);

        // Get user input
        System.out.print("What file would you like to analyze: ");
        String fileName = scan.nextLine();

        System.out.print("What azimuth threshold was used for this test ride: ");
        int azThres = scan.nextInt();


        FileReader fr = new FileReader(fileName);
        BufferedReader br = new BufferedReader(fr);
        int numCycles = 0;
        int bigTurns = 0;
        String line = br.readLine();
        double startBat = 0.0;
        double endBat = 0.0;
        double currBat = 0.0;
        double lastAz = 500.0;
        double currAz = 0.0;
        boolean gpsOff = true;
        boolean initiallyFound = false;

        
        while(line != null){
            if(line.equals("--GPS STARTED--")){
                gpsOff = false;
                numCycles++;
            }
            else if(line.equals("--GPS STOPPED--"))
                gpsOff = true;

            if(!Character.isDigit(line.charAt(0))){
                line = br.readLine();
                continue;
            }
            currBat = Double.parseDouble(line.split(",")[15]);
            currAz = Double.parseDouble(line.split(",")[11]);
            if(startBat == 0.0 && currBat > 0.0)
                startBat = currBat;

            if(lastAz == 500.0 && currAz != 0.0){
                lastAz = currAz;
                initiallyFound = true;
            }

            if(gpsOff && initiallyFound && Math.abs(Math.abs(currAz)-Math.abs(lastAz)) > azThres){
                bigTurns++;
                lastAz = currAz;
            }

            line = br.readLine();
        }

        endBat = currBat;
        System.out.println("\n\n\n\n\nThe GPS turned on " + numCycles + " times.");
        System.out.println("There were " + bigTurns + " big turns.");
        System.out.println("Change in battery: " + (startBat-endBat) + "\n\n\n\n\n");
        br.close();
        scan.close();
    }
}
